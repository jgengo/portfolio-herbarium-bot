# herbabot/config.py
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    PLANTNET_API_KEY: str
    PLANTNET_API_URL: str = "https://my-api.plantnet.org/v2/identify/all"
    GITHUB_TOKEN: str | None = None
    GITHUB_REPO_URL: str | None = None
    GITHUB_REPO_OWNER: str | None = None
    GITHUB_REPO_NAME: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


try:
    settings = Settings()
except ValidationError as e:  # pragma: no cover - config validation
    missing = ", ".join(error["loc"][0] for error in e.errors())
    raise ValueError(f"Missing required environment variables: {missing}") from None

TELEGRAM_BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
PLANTNET_API_KEY = settings.PLANTNET_API_KEY
PLANTNET_API_URL = settings.PLANTNET_API_URL
GITHUB_TOKEN = settings.GITHUB_TOKEN
GITHUB_REPO_URL = settings.GITHUB_REPO_URL
GITHUB_REPO_OWNER = settings.GITHUB_REPO_OWNER
GITHUB_REPO_NAME = settings.GITHUB_REPO_NAME
