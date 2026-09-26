"""PostgreSQL-only tests. Require an empty, dedicated database named kltn_test."""
import asyncio
import os
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4
from typing import Any

from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from sqlalchemy import Connection, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.security import generate_refresh_token, hash_refresh_token
from app.models import AuthSession, User
from app.models.enums import AccountStatus, SystemRole
from app.repositories.auth_session_repository import AuthSessionRepository
from app.repositories.user_repository import UserRepository

BACKEND = Path(__file__).resolve().parents[1]
_original_database_url: str | None = None
_test_url: str = ""


def migration_config() -> Config:
    return Config(str(BACKEND / "alembic.ini"))


async def assert_empty_test_database() -> None:
    engine = create_async_engine(_test_url, poolclass=NullPool)
    try:
        async with engine.connect() as connection:
            tables = await connection.run_sync(lambda c: inspect(c).get_table_names())
            if set(tables) - {"alembic_version", "users", "auth_sessions"}:
                raise RuntimeError("Test database contains unrelated tables; refusing to migrate")
            for table in ("users", "auth_sessions"):
                if table in tables:
                    count = await connection.scalar(select(text("count(*)")).select_from(User.__table__ if table == "users" else AuthSession.__table__))
                    if count:
                        raise RuntimeError("Test database contains account data; refusing destructive migration tests")
    finally:
        await engine.dispose()


def setUpModule() -> None:
    global _test_url, _original_database_url
    _test_url = os.environ.get("TEST_DATABASE_URL") or dotenv_values(BACKEND / ".env").get("TEST_DATABASE_URL") or ""
    if not _test_url:
        raise RuntimeError("Set TEST_DATABASE_URL to a dedicated PostgreSQL kltn_test database")
    test_url = make_url(_test_url)
    development_url = make_url(str(get_settings().database_url))
    if test_url.database != "kltn_test" or test_url.drivername != "postgresql+asyncpg" or test_url.database == development_url.database:
        raise RuntimeError("Refusing database tests outside the dedicated kltn_test database")
    asyncio.run(assert_empty_test_database())
    _original_database_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = _test_url
    get_settings.cache_clear()
    command.upgrade(migration_config(), "head")


def tearDownModule() -> None:
    if _original_database_url is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = _original_database_url
    get_settings.cache_clear()


class MigrationTests(unittest.TestCase):
    def test_upgrade_downgrade_upgrade_and_metadata_match(self) -> None:
        config = migration_config()
        command.check(config)
        command.downgrade(config, "base")

        async def verify_base() -> None:
            engine = create_async_engine(_test_url, poolclass=NullPool)
            try:
                async with engine.connect() as connection:
                    tables = await connection.run_sync(lambda c: inspect(c).get_table_names())
                    self.assertEqual(set(tables), {"alembic_version"})
            finally:
                await engine.dispose()

        asyncio.run(verify_base())
        command.upgrade(config, "head")
        command.check(config)


class RepositoryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine(_test_url, poolclass=NullPool)
        self.connection = await self.engine.connect()
        self.transaction = await self.connection.begin()
        self.session = AsyncSession(bind=self.connection, expire_on_commit=False, join_transaction_mode="create_savepoint")
        self.users = UserRepository(self.session)
        self.sessions = AuthSessionRepository(self.session)

    async def asyncTearDown(self) -> None:
        await self.session.close()
        await self.transaction.rollback()
        await self.connection.close()
        await self.engine.dispose()

    async def create_user(self) -> User:
        return await self.users.create(full_name="Foundation test", email=f"{uuid4()}@example.com", password_hash="test-hash-not-used-for-authentication")

    async def create_session(self, user_id: UUID, *, expires_at: datetime | None = None) -> AuthSession:
        return await self.sessions.create(user_id=user_id, refresh_token_hash=hash_refresh_token(generate_refresh_token()), expires_at=expires_at or datetime.now(UTC) + timedelta(days=7))

    async def test_schema_constraints_and_timestamp_types(self) -> None:
        def inspect_schema(connection: Connection) -> dict[str, Any]:
            inspector = inspect(connection)
            return {
                "users": inspector.get_columns("users"),
                "sessions": inspector.get_columns("auth_sessions"),
                "indexes": inspector.get_indexes("auth_sessions"),
                "foreign_keys": inspector.get_foreign_keys("auth_sessions"),
                "checks": inspector.get_check_constraints("users"),
            }
        schema = await self.connection.run_sync(inspect_schema)
        self.assertEqual({c["name"] for c in schema["users"]}, {"id", "full_name", "email", "password_hash", "status", "system_role", "created_at", "updated_at"})
        for columns in (schema["users"], schema["sessions"]):
            for column in columns:
                if column["name"].endswith("_at"):
                    self.assertTrue(column["type"].timezone)
        self.assertIn("ix_auth_sessions_user_id", {i["name"] for i in schema["indexes"]})
        self.assertEqual(schema["foreign_keys"][0]["referred_table"], "users")
        self.assertEqual({c["name"] for c in schema["checks"]}, {"ck_users_email_normalized", "ck_users_status", "ck_users_system_role"})

    async def test_user_defaults_normalization_update_and_lookup(self) -> None:
        user = await self.users.create(full_name="Initial", email=" Test@Example.COM ", password_hash="test-hash")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.status, AccountStatus.ACTIVE)
        self.assertEqual(user.system_role, SystemRole.USER)
        self.assertIsNotNone(user.created_at.tzinfo)
        self.assertIsNotNone(user.updated_at.tzinfo)
        self.assertEqual((await self.users.get_by_email(" TEST@example.com ")).id, user.id)
        self.assertEqual((await self.users.get_by_id(user.id, for_update=True)).id, user.id)
        await self.users.update_full_name(user, "Updated")
        await self.users.update_password_hash(user, "updated-test-hash")
        self.assertEqual(user.full_name, "Updated")
        self.assertEqual(user.password_hash, "updated-test-hash")

    async def test_unique_email_enum_and_normalization_constraints(self) -> None:
        user = await self.create_user()
        with self.assertRaises(IntegrityError):
            async with self.session.begin_nested():
                await self.users.create(full_name="Duplicate", email=user.email.upper(), password_hash="test-hash")
        for values in ({"status": "OTHER"}, {"system_role": "OWNER"}, {"email": "UPPER@example.com"}):
            with self.assertRaises(IntegrityError):
                async with self.session.begin_nested():
                    await self.session.execute(User.__table__.update().where(User.id == user.id).values(**values))

    async def test_session_unique_hash_and_foreign_key(self) -> None:
        user = await self.create_user()
        auth_session = await self.create_session(user.id)
        with self.assertRaises(IntegrityError):
            async with self.session.begin_nested():
                await self.sessions.create(user_id=user.id, refresh_token_hash=auth_session.refresh_token_hash, expires_at=auth_session.expires_at)
        with self.assertRaises(IntegrityError):
            async with self.session.begin_nested():
                await self.create_session(uuid4())

    async def test_rotation_keeps_session_id_and_rejects_stale_hash(self) -> None:
        user = await self.create_user()
        auth_session = await self.create_session(user.id)
        old_hash = auth_session.refresh_token_hash
        new_hash = hash_refresh_token(generate_refresh_token())
        now = datetime.now(UTC)
        rotated = await self.sessions.rotate_refresh_token(session_id=auth_session.id, expected_hash=old_hash, new_hash=new_hash, expires_at=now + timedelta(days=7), now=now)
        self.assertEqual(rotated.id, auth_session.id)
        self.assertEqual(rotated.refresh_token_hash, new_hash)
        self.assertIsNone(await self.sessions.get_by_refresh_token_hash(old_hash))
        self.assertEqual((await self.sessions.get_by_refresh_token_hash(new_hash, for_update=True)).id, auth_session.id)
        self.assertIsNone(await self.sessions.rotate_refresh_token(session_id=auth_session.id, expected_hash=old_hash, new_hash=hash_refresh_token(generate_refresh_token()), expires_at=now + timedelta(days=7), now=now))

    async def test_expired_or_revoked_sessions_cannot_rotate(self) -> None:
        user = await self.create_user()
        now = datetime.now(UTC)
        expired = await self.create_session(user.id, expires_at=now - timedelta(seconds=1))
        revoked = await self.create_session(user.id)
        await self.sessions.revoke(revoked.id, now=now)
        for auth_session in (expired, revoked):
            self.assertIsNone(await self.sessions.rotate_refresh_token(session_id=auth_session.id, expected_hash=auth_session.refresh_token_hash, new_hash=hash_refresh_token(generate_refresh_token()), expires_at=now + timedelta(days=7), now=now))

    async def test_revoke_other_sessions_preserves_current_and_other_users(self) -> None:
        user, other_user = await self.create_user(), await self.create_user()
        current = await self.create_session(user.id)
        other = await self.create_session(user.id)
        unrelated = await self.create_session(other_user.id)
        await self.sessions.revoke_other_sessions(user.id, current.id, now=datetime.now(UTC))
        for auth_session in (current, other, unrelated):
            await self.session.refresh(auth_session)
        self.assertIsNone(current.revoked_at)
        self.assertIsNotNone(other.revoked_at)
        self.assertIsNone(unrelated.revoked_at)

    async def test_caller_rollback_undoes_user_and_session_writes(self) -> None:
        user = await self.create_user()
        user_id = user.id
        auth_session = await self.create_session(user_id)
        session_id = auth_session.id
        await self.session.rollback()
        self.assertIsNone(await self.users.get_by_id(user_id))
        self.assertIsNone(await self.sessions.get_by_id(session_id))
