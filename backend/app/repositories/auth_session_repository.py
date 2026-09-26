from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth_session import AuthSession


class AuthSessionRepository:
    """Query/update sessions within the transaction owned by the caller."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self, *, user_id: UUID, refresh_token_hash: str, expires_at: datetime,
    ) -> AuthSession:
        auth_session = AuthSession(
            user_id=user_id, refresh_token_hash=refresh_token_hash, expires_at=expires_at,
        )
        self.session.add(auth_session)
        await self.session.flush()
        await self.session.refresh(auth_session)
        return auth_session

    async def get_by_id(self, session_id: UUID, *, for_update: bool = False) -> AuthSession | None:
        statement = select(AuthSession).where(AuthSession.id == session_id)
        if for_update:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        return await self.session.scalar(statement)

    async def get_by_refresh_token_hash(
        self, token_hash: str, *, for_update: bool = False,
    ) -> AuthSession | None:
        statement = select(AuthSession).where(AuthSession.refresh_token_hash == token_hash)
        if for_update:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        return await self.session.scalar(statement)

    async def rotate_refresh_token(
        self, *, session_id: UUID, expected_hash: str, new_hash: str,
        expires_at: datetime, now: datetime,
    ) -> AuthSession | None:
        """Compare-and-swap prevents concurrent requests from reusing the old hash."""
        statement = (
            update(AuthSession)
            .where(
                AuthSession.id == session_id,
                AuthSession.refresh_token_hash == expected_hash,
                AuthSession.revoked_at.is_(None),
                AuthSession.expires_at > now,
            )
            .values(refresh_token_hash=new_hash, expires_at=expires_at, updated_at=now)
            .returning(AuthSession)
            .execution_options(populate_existing=True)
        )
        return await self.session.scalar(statement)

    async def revoke(self, session_id: UUID, *, now: datetime) -> None:
        await self.session.execute(
            update(AuthSession)
            .where(AuthSession.id == session_id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=now, updated_at=now)
        )

    async def revoke_other_sessions(self, user_id: UUID, current_session_id: UUID, *, now: datetime) -> None:
        await self.session.execute(
            update(AuthSession)
            .where(
                AuthSession.user_id == user_id,
                AuthSession.id != current_session_id,
                AuthSession.revoked_at.is_(None),
            )
            .values(revoked_at=now, updated_at=now)
        )
