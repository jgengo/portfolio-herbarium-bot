# herbabot/config.py
import os

from dotenv import load_dotenv

# Load .env file into environment variables
load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Plant Identification
PLANTNET_API_KEY = os.getenv("PLANTNET_API_KEY")
PLANTNET_API_URL = os.getenv(
    "PLANTNET_API_URL", "https://my-api.plantnet.org/v2/identify/all"
)


required = {
    "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    "PLANTNET_API_KEY": PLANTNET_API_KEY,
    "PLANTNET_API_URL": PLANTNET_API_URL,
}

missing = [k for k, v in required.items() if not v]
if missing:
    raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
