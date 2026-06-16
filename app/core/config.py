from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "ABIZ Global Services POS System"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/abiz_pos",
        description="SQLAlchemy database URL for PostgreSQL.",
    )
    secret_key: str = Field(
        default="change-this-secret-key",
        description="Secret key used to sign JWT access tokens.",
    )
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
