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
    access_token_expire_minutes: int = 52560000
    algorithm: str = "HS256"
    backend_cors_origins: str = Field(
        default="http://127.0.0.1:8000,http://localhost:8000",
        description="Comma-separated frontend origins allowed to call the API.",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.backend_cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql+psycopg://", 1)
        return self.database_url

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
