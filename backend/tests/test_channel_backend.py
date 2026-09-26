"""Phase 3B1 targeted verification; fixtures always roll back on kltn_test."""
import asyncio
import os
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from sqlalchemy import inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.models import AuthSession, Channel, User
from app.models.enums import ChannelType, WorkspaceRole
from app.repositories.workspace_member_repository import WorkspaceMemberRepository
from app.schemas.channel import ChannelCreateRequest, ChannelUpdateRequest
from app.schemas.workspace import WorkspaceCreateRequest
from app.services.auth_service import Principal
from app.services.channel_service import ChannelService
from app.services.workspace_service import WorkspaceService

BACKEND = Path(__file__).resolve().parents[1]
_original_url = None
_test_url = ""


def setUpModule():
    global _original_url, _test_url
    _test_url = os.environ.get("TEST_DATABASE_URL") or dotenv_values(BACKEND / ".env").get("TEST_DATABASE_URL") or ""
    url = make_url(_test_url)
    if url.database != "kltn_test" or url.drivername != "postgresql+asyncpg" or url.database == make_url(str(get_settings().database_url)).database:
        raise RuntimeError("Requires dedicated kltn_test PostgreSQL database")

    async def guard():
        engine = create_async_engine(_test_url, poolclass=NullPool)
        try:
            async with engine.begin() as connection:
                tables = set(await connection.run_sync(lambda conn: inspect(conn).get_table_names()))
                allowed = {
                    "alembic_version", "users", "auth_sessions", "workspaces", "workspace_members",
                    "workspace_invitations", "channels", "chat_messages", "chat_attachments", "message_reactions",
                }
                if tables - allowed:
                    raise RuntimeError("Unrelated tables in test database")
                if "workspaces" in tables:
                    # Recover only this test's fixtures after an interrupted migration run.
                    await connection.execute(text(
                        "DELETE FROM workspaces WHERE name IN ('Legacy empty', 'Legacy general')"
                    ))
                for table in ("channels", "chat_messages", "chat_attachments", "message_reactions"):
                    if table in tables and await connection.scalar(text(f"SELECT count(*) FROM {table}")):
                        raise RuntimeError("Phase 3 test tables must be empty before migration verification")
        finally:
            await engine.dispose()

    asyncio.run(guard())
    _original_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = _test_url
    get_settings.cache_clear()
    config = Config(str(BACKEND / "alembic.ini"))
    command.upgrade(config, "20260926_01")

    first, second = uuid4(), uuid4()

    async def insert_legacy_workspaces():
        engine = create_async_engine(_test_url, poolclass=NullPool)
        try:
            async with engine.begin() as connection:
                await connection.execute(text(
                    "INSERT INTO workspaces (id, name) VALUES (:first, 'Legacy empty'), (:second, 'Legacy general')"
                ), {"first": first, "second": second})
                await connection.execute(text(
                    "INSERT INTO channels (id, workspace_id, name, type, is_default) "
                    "VALUES (:id, :workspace, 'general', 'TEXT', false)"
                ), {"id": uuid4(), "workspace": second})
        finally:
            await engine.dispose()

    async def verify_and_cleanup_backfill():
        engine = create_async_engine(_test_url, poolclass=NullPool)
        try:
            async with engine.begin() as connection:
                rows = (await connection.execute(text(
                    "SELECT workspace_id, count(*) AS total, count(*) FILTER (WHERE is_default) AS defaults, "
                    "count(*) FILTER (WHERE name = 'general' AND type = 'TEXT') AS general "
                    "FROM channels WHERE workspace_id IN (:first, :second) GROUP BY workspace_id"
                ), {"first": first, "second": second})).mappings().all()
                if len(rows) != 2 or any(row["total"] != 1 or row["defaults"] != 1 or row["general"] != 1 for row in rows):
                    raise AssertionError("Legacy workspace default-channel backfill failed")
                await connection.execute(text("DELETE FROM workspaces WHERE id IN (:first, :second)"), {"first": first, "second": second})
        finally:
            await engine.dispose()

    asyncio.run(insert_legacy_workspaces())
    command.upgrade(config, "head")
    command.downgrade(config, "20260926_01")
    command.upgrade(config, "head")
    asyncio.run(verify_and_cleanup_backfill())
    command.check(config)


def tearDownModule():
    if _original_url is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = _original_url
    get_settings.cache_clear()


class ChannelBackendTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine(_test_url, poolclass=NullPool)
        self.connection = await self.engine.connect()
        self.outer_transaction = await self.connection.begin()
        self.session = AsyncSession(bind=self.connection, expire_on_commit=False, join_transaction_mode="create_savepoint")
        users = [User(full_name=f"Channel user {index}", email=f"{uuid4()}@example.com", password_hash="unused") for index in range(4)]
        self.session.add_all(users)
        await self.session.flush()
        sessions = [AuthSession(
            user_id=user.id, refresh_token_hash=uuid4().hex + uuid4().hex,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        ) for user in users]
        self.session.add_all(sessions)
        await self.session.commit()
        self.principals = [Principal(user=SimpleNamespace(id=user.id), session=SimpleNamespace(id=session.id)) for user, session in zip(users, sessions)]
        self.owner, self.admin, self.member, self.outsider = self.principals
        self.workspace_service = WorkspaceService(self.session)
        self.channel_service = ChannelService(self.session)
        workspace_response = await self.workspace_service.create(
            self.owner, WorkspaceCreateRequest(name="Channel backend", description=None),
        )
        self.workspace_id = workspace_response.id
        members = WorkspaceMemberRepository(self.session)
        async with self.session.begin():
            await members.create(workspace_id=self.workspace_id, user_id=self.admin.user.id, role=WorkspaceRole.ADMIN)
            await members.create(workspace_id=self.workspace_id, user_id=self.member.user.id, role=WorkspaceRole.MEMBER)

    async def asyncTearDown(self):
        await self.session.close()
        await self.outer_transaction.rollback()
        await self.connection.close()
        await self.engine.dispose()

    async def assert_app_error(self, code, awaitable):
        with self.assertRaises(AppError) as caught:
            await awaitable
        self.assertEqual(caught.exception.code, code)

    async def test_workspace_creation_has_exact_default_general(self):
        channels = await self.channel_service.list(self.owner, self.workspace_id)
        defaults = [channel for channel in channels if channel.is_default]
        self.assertEqual(len(defaults), 1)
        self.assertEqual(defaults[0].name, "general")
        self.assertEqual(defaults[0].type, ChannelType.TEXT)

    async def test_create_permissions_duplicate_and_type(self):
        owner_channel = await self.channel_service.create(
            self.owner, self.workspace_id, ChannelCreateRequest(name="backend", description="Backend", type="TEXT"),
        )
        admin_channel = await self.channel_service.create(
            self.admin, self.workspace_id, ChannelCreateRequest(name="study", description=None, type="STUDY_ROOM"),
        )
        self.assertEqual(owner_channel.type, ChannelType.TEXT)
        self.assertEqual(admin_channel.type, ChannelType.STUDY_ROOM)
        await self.assert_app_error("CHANNEL_PERMISSION_DENIED", self.channel_service.create(
            self.member, self.workspace_id, ChannelCreateRequest(name="denied", description=None, type="TEXT"),
        ))
        await self.assert_app_error("CHANNEL_NAME_ALREADY_EXISTS", self.channel_service.create(
            self.owner, self.workspace_id, ChannelCreateRequest(name="backend", description=None, type="TEXT"),
        ))
        await self.assert_app_error("INVALID_CHANNEL_TYPE", self.channel_service.create(
            self.owner, self.workspace_id, ChannelCreateRequest(name="invalid", description=None, type="VOICE"),
        ))

    async def test_list_detail_and_update_permissions(self):
        first = await self.channel_service.create(
            self.owner, self.workspace_id, ChannelCreateRequest(name="first", description=None, type="TEXT"),
        )
        second = await self.channel_service.create(
            self.owner, self.workspace_id, ChannelCreateRequest(name="second", description=None, type="TEXT"),
        )
        self.assertIn(first.id, {channel.id for channel in await self.channel_service.list(self.member, self.workspace_id)})
        self.assertEqual((await self.channel_service.detail(self.member, first.id)).id, first.id)
        await self.assert_app_error("CHANNEL_PERMISSION_DENIED", self.channel_service.detail(self.outsider, first.id))
        updated = await self.channel_service.update(self.owner, first.id, ChannelUpdateRequest(name="owner-edit"))
        self.assertEqual(updated.name, "owner-edit")
        updated = await self.channel_service.update(self.admin, second.id, ChannelUpdateRequest(description="Admin edit"))
        self.assertEqual(updated.description, "Admin edit")
        await self.assert_app_error("CHANNEL_PERMISSION_DENIED", self.channel_service.update(
            self.member, first.id, ChannelUpdateRequest(description="Denied"),
        ))

    async def test_delete_permissions_and_default_protection(self):
        owner_channel = await self.channel_service.create(
            self.owner, self.workspace_id, ChannelCreateRequest(name="owner-delete", description=None, type="TEXT"),
        )
        admin_channel = await self.channel_service.create(
            self.owner, self.workspace_id, ChannelCreateRequest(name="admin-delete", description=None, type="TEXT"),
        )
        member_channel = await self.channel_service.create(
            self.owner, self.workspace_id, ChannelCreateRequest(name="member-denied", description=None, type="TEXT"),
        )
        await self.channel_service.delete(self.owner, owner_channel.id)
        await self.channel_service.delete(self.admin, admin_channel.id)
        await self.assert_app_error("CHANNEL_PERMISSION_DENIED", self.channel_service.delete(self.member, member_channel.id))
        general = next(channel for channel in await self.channel_service.list(self.owner, self.workspace_id) if channel.is_default)
        await self.assert_app_error("DEFAULT_CHANNEL_CANNOT_BE_DELETED", self.channel_service.delete(self.owner, general.id))
        async with self.session.begin():
            remaining = await self.session.scalar(select(Channel).where(Channel.id == member_channel.id))
            deleted = await self.session.scalar(select(Channel).where(Channel.id == owner_channel.id))
        self.assertIsNotNone(remaining)
        self.assertIsNone(deleted)

    async def test_routes_and_backend_startup(self):
        from app.main import app
        expected = {
            ("POST", "/api/v1/workspaces/{workspace_id}/channels"),
            ("GET", "/api/v1/workspaces/{workspace_id}/channels"),
            ("GET", "/api/v1/channels/{channel_id}"),
            ("PATCH", "/api/v1/channels/{channel_id}"),
            ("DELETE", "/api/v1/channels/{channel_id}"),
        }
        async with app.router.lifespan_context(app):
            schema = app.openapi()
            routes = {
                (method.upper(), path)
                for path, operations in schema["paths"].items()
                for method in operations
            }
            self.assertTrue(expected <= routes, expected - routes)
