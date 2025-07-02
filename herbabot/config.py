import logging

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    telegram_bot_token: str
    plantnet_api_key: str
    plantnet_api_url: str = "https://my-api.plantnet.org/v2/identify/all"
    github_token: str
    github_repo_url: str
    github_repo_owner: str
    github_repo_name: str
    allowed_user_ids: str = ""
    logging_level: str = "WARNING"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


config = Config()  # type: ignore

TELEGRAM_BOT_TOKEN = config.telegram_bot_token
PLANTNET_API_KEY = config.plantnet_api_key
PLANTNET_API_URL = config.plantnet_api_url
GITHUB_TOKEN = config.github_token
GITHUB_REPO_URL = config.github_repo_url
GITHUB_REPO_OWNER = config.github_repo_owner
GITHUB_REPO_NAME = config.github_repo_name
LOGGING_LEVEL = config.logging_level


def get_logging_level() -> int:
    valid_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    level = LOGGING_LEVEL.upper()
    if level not in valid_levels:
        print(f"Warning: Invalid logging level '{LOGGING_LEVEL}'. Using WARNING.")
        return logging.WARNING

    return valid_levels[level]


def get_allowed_user_ids() -> list[int]:
    if not config.allowed_user_ids:
        return []

    try:
        return [int(uid.strip()) for uid in config.allowed_user_ids.split(",") if uid.strip()]
    except ValueError:
        return []


ALLOWED_USER_IDS = get_allowed_user_ids()
