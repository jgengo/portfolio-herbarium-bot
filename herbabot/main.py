import logging

from telegram.ext import ApplicationBuilder

from herbabot.config import TELEGRAM_BOT_TOKEN, get_logging_level
from herbabot.handlers import register_handlers

logging.basicConfig(level=get_logging_level())


def main() -> None:
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    register_handlers(app)
    print("🤖 Herbabot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
