import asyncio
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID

import jwt
from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.config import get_settings

_password_hasher = PasswordHasher(type=Type.ID)
_dummy_password_hash = _password_hasher.hash(secrets.token_urlsafe(32))
_JWT_ALGORITHM = "HS256"


class AccessTokenClaims(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    sub: UUID
    sid: UUID
    type: Literal["access"]
    iat: int = Field(strict=True, ge=0)
    exp: int = Field(strict=True, ge=0)


async def hash_password(password: str) -> str:
    """Run Argon2id outside the event loop; do not trim or normalize passwords."""
    if not 8 <= len(password) <= 128:
        raise ValueError("Password must contain between 8 and 128 characters")
    return await asyncio.to_thread(_password_hasher.hash, password)


async def verify_password(password: str, password_hash: str) -> bool:
    if not 8 <= len(password) <= 128:
        return False
    try:
        return await asyncio.to_thread(_password_hasher.verify, password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


async def verify_login_password(password: str, password_hash: str | None) -> bool:
    """Perform Argon2 verification even when the account does not exist."""
    verified = await verify_password(password, password_hash or _dummy_password_hash)
    return password_hash is not None and verified


def create_access_token(user_id: UUID, session_id: UUID) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    claims = AccessTokenClaims(
        sub=user_id, sid=session_id, type="access",
        iat=int(now.timestamp()),
        exp=int((now + timedelta(minutes=settings.access_token_expire_minutes)).timestamp()),
    )
    return jwt.encode(
        claims.model_dump(mode="json"), settings.jwt_secret_key.get_secret_value(),
        algorithm=_JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> AccessTokenClaims:
    """Validate signature/claims only; database session/user checks belong to Phase 1B."""
    payload = jwt.decode(
        token, get_settings().jwt_secret_key.get_secret_value(), algorithms=[_JWT_ALGORITHM],
        options={"require": ["sub", "sid", "type", "iat", "exp"]},
    )
    try:
        claims = AccessTokenClaims.model_validate(payload)
    except ValidationError:
        raise jwt.InvalidTokenError("Invalid access token claims") from None
    if claims.exp <= claims.iat:
        raise jwt.InvalidTokenError("Invalid access token lifetime")
    return claims


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def refresh_token_expires_at() -> datetime:
    return datetime.now(UTC) + timedelta(days=get_settings().refresh_token_expire_days)
