from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.normalization import normalize_email
from app.models.user import User


class UserRepository:
    """Database operations; the caller owns commit/rollback and business validation."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: UUID, *, for_update: bool = False) -> User | None:
        statement = select(User).where(User.id == user_id)
        if for_update:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        return await self.session.scalar(statement)

    async def get_by_email(self, email: str, *, for_update: bool = False) -> User | None:
        statement = select(User).where(User.email == normalize_email(email))
        if for_update:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        return await self.session.scalar(statement)

    async def create(self, *, full_name: str, email: str, password_hash: str) -> User:
        user = User(full_name=full_name, email=normalize_email(email), password_hash=password_hash)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    @staticmethod
    def is_email_conflict(exc: IntegrityError) -> bool:
        cause = exc.orig.__cause__
        return (
            getattr(exc.orig, "sqlstate", None) == "23505"
            and getattr(cause, "constraint_name", None) == "users_email_key"
        )

    async def update_full_name(self, user: User, full_name: str) -> User:
        user.full_name = full_name
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update_password_hash(self, user: User, password_hash: str) -> None:
        user.password_hash = password_hash
        await self.session.flush()
        await self.session.refresh(user)
