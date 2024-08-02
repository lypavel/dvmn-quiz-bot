from logging import Formatter, Handler, LogRecord

from telegram import Bot


class TelegramLogsHandler(Handler):
    def __init__(self, tg_bot_token, chat_id) -> None:
        super().__init__()

        self.chat_id = chat_id
        self.bot = Bot(token=tg_bot_token)

        self.setFormatter(Formatter('[%(name)s][%(levelname)s]: %(message)s'))

    def emit(self, record: LogRecord) -> None:
        log_entry = self.format(record)

        self.bot.send_message(
            self.chat_id,
            log_entry
        )
