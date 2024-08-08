from telegram import ReplyKeyboardMarkup

BUTTONS = {
    'new_question': 'Новый вопрос',
    'surrender': 'Сдаться',
    'my_score': 'Мой счёт'
}

MESSAGES = {
    'greeting': 'Привет! Я бот для викторин!',
    'how_to_stop': 'Для остановки викторины используйте команду \"/stop\"',
    'correct_answer': 'Правильно! Поздравляю!',
    'wrong_answer': 'Неправильно... Попробуешь ещё раз?',
    'get_new_question': 'Для нового вопроса нажми \"Новый вопрос\".',
    'surrender': 'Если затрудняешься с ответом, нажми \"Сдаться\".',
    'answer': 'Ответ',
    'no_active_question': 'У вас нет активного вопроса.',
    'game_stopped': 'Викторина остановлена. '
    'Для возобновления используйте команду \"/start\"',
}

TG_REPLY_KEYBOARD = [
    [BUTTONS['new_question'], BUTTONS['surrender']],
    [BUTTONS['my_score']]
]

TG_REPLY_MARKUP = ReplyKeyboardMarkup(TG_REPLY_KEYBOARD)
