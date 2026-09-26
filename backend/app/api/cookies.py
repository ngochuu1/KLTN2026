from datetime import datetime

from fastapi import Response
from pydantic import SecretStr

from app.core.config import get_settings

_REFRESH_PATH = "/api/v1/auth"


def set_refresh_cookie(response: Response, token: SecretStr, expires_at: datetime) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.refresh_cookie_name, value=token.get_secret_value(),
        max_age=settings.refresh_token_expire_days * 86400, expires=expires_at,
        path=_REFRESH_PATH, secure=settings.cookie_secure, httponly=True, samesite="lax",
    )
    response.headers["Cache-Control"] = "no-store"


def clear_refresh_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=settings.refresh_cookie_name, path=_REFRESH_PATH,
        secure=settings.cookie_secure, httponly=True, samesite="lax",
    )
    response.headers["Cache-Control"] = "no-store"
