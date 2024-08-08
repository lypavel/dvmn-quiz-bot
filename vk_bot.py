import logging
from random import choice, randint

from environs import Env
import redis
import vk_api as vk
from vk_api.keyboard import VkKeyboard
from vk_api.longpoll import VkLongPoll, VkEventType, Event
from vk_api.vk_api import VkApiMethod

from bot_strings import BUTTONS, MESSAGES
from logs_handler import TelegramLogsHandler
from questions import check_answer, get_questions_with_answers, \
    get_questions_list

logger = logging.getLogger(__file__)


def create_keyboard():
    keyboard = VkKeyboard()

    keyboard.add_button(BUTTONS['new_question'])
    keyboard.add_button(BUTTONS['surrender'])

    keyboard.add_line()
    keyboard.add_button(BUTTONS['my_score'])

    return keyboard.get_keyboard()


def start(event: Event, vk_api: VkApiMethod, redis_db: redis.Redis) -> None:
    redis_db.set(f'vk_{event.user_id}', '')

    vk_api.messages.send(
        user_id=event.user_id,
        message=f'{MESSAGES["greeting"]} {MESSAGES["get_new_question"]}',
        random_id=randint(1, 1000),
        keyboard=create_keyboard()
    )


def handle_new_question_request(event: Event,
                                vk_api: VkApiMethod,
                                questions_list: list[str],
                                redis_db: redis.Redis) -> None:
    question = choice(questions_list)

    redis_db.set(f'vk_{event.user_id}', question)

    vk_api.messages.send(
        user_id=event.user_id,
        message=question,
        random_id=randint(1, 1000)
    )


def handle_surrender_request(event: Event,
                             vk_api: VkApiMethod,
                             questions_with_answers: dict,
                             redis_db: redis.Redis) -> None:
    question = redis_db.get(f'vk_{event.user_id}')
    correct_answer = questions_with_answers.get(question)

    redis_db.set(f'vk_{event.user_id}', '')

    vk_api.messages.send(
        user_id=event.user_id,
        message=f'{MESSAGES["answer"]}:\n{correct_answer}\n\n'
        f'{MESSAGES["get_new_question"]}',
        random_id=randint(1, 1000)
    )


def handle_solution_attempt(event: Event,
                            vk_api: VkApiMethod,
                            questions_with_answers: dict,
                            redis_db: redis.Redis) -> None:
    question = redis_db.get(f'vk_{event.user_id}')
    correct_answer = questions_with_answers.get(question)

    if check_answer(event.text, correct_answer):
        redis_db.set(f'vk_{event.user_id}', '')

        vk_api.messages.send(
            user_id=event.user_id,
            message=f'{MESSAGES["correct_answer"]} '
            f'{MESSAGES["get_new_question"]}',
            random_id=randint(1, 1000)
        )
        return

    vk_api.messages.send(
        user_id=event.user_id,
        message=f'{MESSAGES["wrong_answer"]} {MESSAGES["surrender"]}',
        random_id=randint(1, 1000)
    )


def main():
    env = Env()
    env.read_env()

    tg_bot_token = env.str('TG_BOT_TOKEN')
    tg_logs_chat_id = env.int('TG_LOGS_CHAT_ID')

    logger.setLevel(logging.INFO)
    logger.addHandler(TelegramLogsHandler(tg_bot_token, tg_logs_chat_id))

    logger.info('VK quiz bot started.')

    redis_host = env.str('REDIS_DB_HOST')
    redis_port = env.int('REDIS_DB_PORT')
    redis_password = env.str('REDIS_DB_PASSWORD', None)

    redis_db = redis.Redis(host=redis_host,
                           port=redis_port,
                           password=redis_password,
                           decode_responses=True)

    all_questions_file = env.str('ALL_QUESTIONS_FILE', 'questions.json')
    questions_with_answers = get_questions_with_answers(all_questions_file)
    questions_list = get_questions_list(questions_with_answers)

    vk_token = env.str('VK_API_TOKEN')
    vk_session = vk.VkApi(token=vk_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    try:
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                current_question = redis_db.get(f'vk_{event.user_id}')
                if current_question is None:
                    start(event, vk_api, redis_db)
                elif not current_question:
                    if event.text == BUTTONS['new_question']:
                        handle_new_question_request(event,
                                                    vk_api,
                                                    questions_list,
                                                    redis_db)
                        continue

                    vk_api.messages.send(
                        user_id=event.user_id,
                        message=f'{MESSAGES["no_active_question"]} '
                        f'{MESSAGES["get_new_question"]}',
                        random_id=randint(1, 1000)
                    )
                elif event.text == BUTTONS['surrender']:
                    handle_surrender_request(event,
                                             vk_api,
                                             questions_with_answers,
                                             redis_db)
                else:
                    handle_solution_attempt(event,
                                            vk_api,
                                            questions_with_answers,
                                            redis_db)
    except Exception as exception:
        logger.exception(exception)


if __name__ == "__main__":
    main()
