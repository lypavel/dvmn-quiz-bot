from enum import Enum
from functools import partial
import logging
from pathlib import Path
from random import choice

from environs import Env
import redis
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, \
    CallbackContext, ConversationHandler

from bot_strings import BUTTONS, MESSAGES, TG_REPLY_MARKUP
from logs_handler import TelegramLogsHandler
from questions import check_answer, get_questions_with_answers, \
    get_questions_list

logger = logging.getLogger(Path(__file__).name)


class BotState(Enum):
    NEW_QUESTION = 0
    AWAIT_ANSWER = 1


def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        f'{MESSAGES["greeting"]} {MESSAGES["get_new_question"]}\n'
        f'{MESSAGES["how_to_stop"]}',
        reply_markup=TG_REPLY_MARKUP,
    )

    return BotState.NEW_QUESTION


def handle_new_question_request(update: Update,
                                context: CallbackContext,
                                questions_list: list[str],
                                redis_db: redis.Redis) -> int:
    question = choice(questions_list)

    redis_db.set(f'tg_{update.effective_user.id}', question)

    update.message.reply_text(
        question,
        reply_markup=TG_REPLY_MARKUP)

    return BotState.AWAIT_ANSWER


def handle_solution_attempt(update: Update,
                            context: CallbackContext,
                            questions_with_answers: dict,
                            redis_db: redis.Redis) -> int:
    question = redis_db.get(f'tg_{update.effective_user.id}')
    correct_answer = questions_with_answers[question]

    if check_answer(update.message.text, correct_answer):
        update.message.reply_text(
            f'{MESSAGES["correct_answer"]} {MESSAGES["get_new_question"]}',
            reply_markup=TG_REPLY_MARKUP)
        return BotState.NEW_QUESTION

    update.message.reply_text(
        f'{MESSAGES["wrong_answer"]} {MESSAGES["surrender"]}',
        reply_markup=TG_REPLY_MARKUP)

    return BotState.AWAIT_ANSWER


def handle_surrender_request(update: Update,
                             context: CallbackContext,
                             questions_with_answers: dict,
                             redis_db: redis.Redis) -> int:
    question = redis_db.get(f'tg_{update.effective_user.id}')
    correct_answer = questions_with_answers[question]

    update.message.reply_text(
        f'{MESSAGES["answer"]}:\n{correct_answer}\n\n'
        f'{MESSAGES["get_new_question"]}',
        reply_markup=TG_REPLY_MARKUP)
    return BotState.NEW_QUESTION


def stop(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        MESSAGES['game_stopped'],
        reply_markup=TG_REPLY_MARKUP,
    )
    return ConversationHandler.END


def main() -> None:
    env = Env()
    env.read_env()
    tg_token = env.str('TG_BOT_TOKEN')
    tg_logs_chat_id = env.int('TG_LOGS_CHAT_ID')

    logger.setLevel(logging.INFO)
    logger.addHandler(TelegramLogsHandler(tg_token, tg_logs_chat_id))

    logger.info('Telegram quiz bot started.')

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

    try:
        updater = Updater(tg_token)
        dispatcher = updater.dispatcher

        conversation_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],

            states={
                BotState.NEW_QUESTION: [
                    MessageHandler(
                        Filters.regex(fr'^{BUTTONS["new_question"]}$'),
                        partial(handle_new_question_request,
                                questions_list=questions_list,
                                redis_db=redis_db),
                    )
                ],

                BotState.AWAIT_ANSWER: [
                    MessageHandler(
                        Filters.regex(fr'^{BUTTONS["surrender"]}$'),
                        partial(
                            handle_surrender_request,
                            questions_with_answers=questions_with_answers,
                            redis_db=redis_db)
                    ),
                    MessageHandler(
                        Filters.text,
                        partial(
                            handle_solution_attempt,
                            questions_with_answers=questions_with_answers,
                            redis_db=redis_db
                        )),
                ]
            },

            fallbacks=[CommandHandler('stop', stop)]
        )

        dispatcher.add_handler(conversation_handler)

        updater.start_polling()
        updater.idle()
    except Exception as exception:
        logger.exception(exception)


if __name__ == '__main__':
    main()
