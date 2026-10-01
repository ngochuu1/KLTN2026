from functools import lru_cache
from pathlib import Path

from typing import Self

from pydantic import AnyHttpUrl, Field, PostgresDsn, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    app_name: str
    app_env: str
    database_url: PostgresDsn
    frontend_url: AnyHttpUrl
    jwt_secret_key: SecretStr
    access_token_expire_minutes: int = Field(default=15, gt=0)
    refresh_token_expire_days: int = Field(default=7, gt=0)
    refresh_cookie_name: str = Field(default="refresh_token", pattern=r"^[A-Za-z0-9_-]+$")
    cookie_secure: bool = False
    object_storage_endpoint: str = ""
    object_storage_access_key: SecretStr = SecretStr("")
    object_storage_secret_key: SecretStr = SecretStr("")
    object_storage_bucket: str = ""
    object_storage_secure: bool = False
    attachment_max_size_bytes: int = Field(default=25 * 1024 * 1024, gt=0)
    livekit_url: str = ""
    livekit_api_key: SecretStr = SecretStr("")
    livekit_api_secret: SecretStr = SecretStr("")

    @field_validator("jwt_secret_key")
    @classmethod
    def require_signing_key(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value().encode("utf-8")) < 32:
            raise ValueError("JWT_SECRET_KEY must contain at least 32 bytes")
        return value

    @model_validator(mode="after")
    def require_secure_production_cookie(self) -> Self:
        if self.app_env.lower() == "production" and not self.cookie_secure:
            raise ValueError("COOKIE_SECURE must be true in production")
        return self

    @field_validator("database_url")
    @classmethod
    def require_asyncpg(cls, value: PostgresDsn) -> PostgresDsn:
        if value.scheme != "postgresql+asyncpg":
            raise ValueError("DATABASE_URL must use postgresql+asyncpg")
        return value

    @field_validator("frontend_url")
    @classmethod
    def require_origin(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        if (
            value.path not in (None, "/")
            or value.query is not None
            or value.fragment is not None
            or value.username is not None
            or value.password is not None
        ):
            raise ValueError("FRONTEND_URL must be an HTTP(S) origin without a path")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
