from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Generic, TypeVar
from uuid import UUID

import jwt
from pydantic import SecretStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.security import (
    create_access_token, decode_access_token, generate_refresh_token, hash_password,
    hash_refresh_token, refresh_token_expires_at, verify_login_password,
)
from app.models import AuthSession, User
from app.models.enums import AccountStatus
from app.repositories.auth_session_repository import AuthSessionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RefreshResponse, RegisterRequest, RegisterResponse, TokenResponse
from app.schemas.user import UserPublic

T = TypeVar("T")


@dataclass(frozen=True)
class Principal:
    user: User
    session: AuthSession


@dataclass(frozen=True)
class TokenGrant(Generic[T]):
    data: T
    refresh_token: SecretStr
    refresh_expires_at: datetime


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.sessions = AuthSessionRepository(db)

    async def register(self, request: RegisterRequest) -> RegisterResponse:
        password_hash = await hash_password(request.password.get_secret_value())
        try:
            async with self.db.begin():
                if await self.users.get_by_email(str(request.email)) is not None:
                    raise AppError(409, "EMAIL_ALREADY_EXISTS", "Email đã được sử dụng")
                user = await self.users.create(
                    full_name=request.full_name, email=str(request.email), password_hash=password_hash,
                )
                result = RegisterResponse.model_validate(user)
        except IntegrityError as exc:
            if self.users.is_email_conflict(exc):
                raise AppError(409, "EMAIL_ALREADY_EXISTS", "Email đã được sử dụng") from None
            raise
        return result

    async def login(self, request: LoginRequest) -> TokenGrant[TokenResponse]:
        async with self.db.begin():
            # All session mutations lock the user before the session, including login.
            user = await self.users.get_by_email(str(request.email), for_update=True)
            valid = await verify_login_password(
                request.password.get_secret_value(), user.password_hash if user else None,
            )
            if not valid or user is None:
                raise AppError(401, "INVALID_CREDENTIALS", "Email hoặc mật khẩu không chính xác")
            self.require_active(user)
            refresh_token = generate_refresh_token()
            expires_at = refresh_token_expires_at()
            session = await self.sessions.create(
                user_id=user.id, refresh_token_hash=hash_refresh_token(refresh_token), expires_at=expires_at,
            )
            result = TokenGrant(
                data=TokenResponse(
                    access_token=create_access_token(user.id, session.id),
                    expires_in=get_settings().access_token_expire_minutes * 60,
                    user=UserPublic.model_validate(user),
                ),
                refresh_token=SecretStr(refresh_token), refresh_expires_at=expires_at,
            )
        return result

    async def refresh(self, refresh_token: str | None) -> TokenGrant[RefreshResponse]:
        if not refresh_token:
            raise AppError(401, "SESSION_INVALID", "Phiên xác thực không hợp lệ")
        token_hash = hash_refresh_token(refresh_token)
        async with self.db.begin():
            candidate = await self.sessions.get_by_refresh_token_hash(token_hash)
            if candidate is None:
                raise AppError(401, "SESSION_INVALID", "Phiên xác thực không hợp lệ")
            principal = await self.load_principal(candidate.user_id, candidate.id)
            new_token = generate_refresh_token()
            expires_at = refresh_token_expires_at()
            rotated = await self.sessions.rotate_refresh_token(
                session_id=principal.session.id, expected_hash=token_hash,
                new_hash=hash_refresh_token(new_token), expires_at=expires_at, now=datetime.now(UTC),
            )
            if rotated is None:
                raise AppError(401, "SESSION_INVALID", "Phiên xác thực không hợp lệ")
            result = TokenGrant(
                data=RefreshResponse(
                    access_token=create_access_token(principal.user.id, rotated.id),
                    expires_in=get_settings().access_token_expire_minutes * 60,
                ),
                refresh_token=SecretStr(new_token), refresh_expires_at=expires_at,
            )
        return result

    async def authenticate(self, access_token: str) -> Principal:
        try:
            claims = decode_access_token(access_token)
        except jwt.ExpiredSignatureError:
            raise AppError(401, "ACCESS_TOKEN_EXPIRED", "Access token đã hết hạn") from None
        except jwt.InvalidTokenError:
            raise AppError(401, "ACCESS_TOKEN_INVALID", "Access token không hợp lệ") from None
        async with self.db.begin():
            principal = await self.load_principal(claims.sub, claims.sid)
        return principal

    async def load_principal(self, user_id: UUID, session_id: UUID) -> Principal:
        """Caller owns the transaction. Always lock user, then session, and reload."""
        user = await self.users.get_by_id(user_id, for_update=True)
        if user is None:
            raise AppError(401, "SESSION_INVALID", "Phiên xác thực không hợp lệ")
        session = await self.sessions.get_by_id(session_id, for_update=True)
        if session is None or session.user_id != user.id or session.revoked_at is not None:
            raise AppError(401, "SESSION_INVALID", "Phiên xác thực không hợp lệ")
        if session.expires_at <= datetime.now(UTC):
            raise AppError(401, "SESSION_EXPIRED", "Phiên xác thực đã hết hạn")
        self.require_active(user)
        return Principal(user=user, session=session)

    async def logout(self, principal: Principal) -> None:
        async with self.db.begin():
            current = await self.load_principal(principal.user.id, principal.session.id)
            await self.sessions.revoke(current.session.id, now=datetime.now(UTC))

    @staticmethod
    def require_active(user: User) -> None:
        if user.status != AccountStatus.ACTIVE:
            raise AppError(403, "ACCOUNT_LOCKED", "Tài khoản đã bị khóa")
