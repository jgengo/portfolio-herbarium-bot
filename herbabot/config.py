# herbabot/config.py
import os

from dotenv import load_dotenv

# Load .env file into environment variables
load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


required = {
    "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
}

missing = [k for k, v in required.items() if not v]
if missing:
    raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
