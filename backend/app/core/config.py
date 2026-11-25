import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def load_local_environment(env_file: Path = ENV_FILE) -> None:
    """Expose .env secrets to provider adapters without overriding shell env vars."""
    load_dotenv(dotenv_path=env_file, override=False)


# Pydantic Settings reads declared app settings. Adapters use dynamically named
# secrets (for example OPENAI_API_KEY), so expose .env values to os.environ too.
load_local_environment()


class Settings(BaseSettings):
    app_name: str = "LLM Reliability Evaluation Harness API"
    app_env: str = "development"
    api_prefix: str = "/api"
    database_url: str | None = None
    database_url_unpooled: str | None = None
    cors_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
