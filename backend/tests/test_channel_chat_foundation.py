"""Phase 3A targeted PostgreSQL verification; fixtures roll back on kltn_test."""
import asyncio
import os
import unittest
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from sqlalchemy import inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.models import ChatAttachment, ChatMessage, Channel, MessageReaction, User, Workspace
from app.models.enums import ChannelType
from app.repositories.channel_repository import ChannelRepository
from app.repositories.chat_attachment_repository import ChatAttachmentRepository
from app.repositories.chat_message_repository import ChatMessageRepository
from app.repositories.message_reaction_repository import MessageReactionRepository

BACKEND = Path(__file__).resolve().parents[1]
PHASE_3_TABLES = {"channels", "chat_messages", "chat_attachments", "message_reactions"}
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
            async with engine.connect() as connection:
                tables = set(await connection.run_sync(lambda conn: inspect(conn).get_table_names()))
                allowed = {"alembic_version", "users", "auth_sessions", "workspaces", "workspace_members", "workspace_invitations"} | PHASE_3_TABLES
                if tables - allowed:
                    raise RuntimeError("Unrelated tables in test database")
                for table in PHASE_3_TABLES & tables:
                    if await connection.scalar(text(f"SELECT count(*) FROM {table}")):
                        raise RuntimeError("Phase 3A test tables must be empty before migration round trip")
        finally:
            await engine.dispose()

    asyncio.run(guard())
    _original_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = _test_url
    get_settings.cache_clear()
    config = Config(str(BACKEND / "alembic.ini"))
    command.upgrade(config, "head")
    command.check(config)
    command.downgrade(config, "20260925_01")
    command.upgrade(config, "head")
    command.check(config)


def tearDownModule():
    if _original_url is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = _original_url
    get_settings.cache_clear()


class ChannelChatFoundationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine(_test_url, poolclass=NullPool)
        self.connection = await self.engine.connect()
        self.transaction = await self.connection.begin()
        self.session = AsyncSession(bind=self.connection, expire_on_commit=False, join_transaction_mode="create_savepoint")
        self.channels = ChannelRepository(self.session)
        self.messages = ChatMessageRepository(self.session)
        self.attachments = ChatAttachmentRepository(self.session)
        self.reactions = MessageReactionRepository(self.session)
        self.user = User(full_name="Chat fixture", email=f"{uuid4()}@example.com", password_hash="unused")
        self.workspace = Workspace(name="Chat foundation")
        self.session.add_all([self.user, self.workspace])
        await self.session.flush()
        self.channel = await self.channels.create(
            workspace_id=self.workspace.id, name="general", type=ChannelType.TEXT, is_default=True,
        )

    async def asyncTearDown(self):
        await self.session.close()
        await self.transaction.rollback()
        await self.connection.close()
        await self.engine.dispose()

    async def rejected(self, statement, params):
        with self.assertRaises(IntegrityError):
            async with self.session.begin_nested():
                await self.session.execute(text(statement), params)

    async def test_channel_repository_and_constraints(self):
        self.assertEqual((await self.channels.get_by_id(self.channel.id, for_update=True)).id, self.channel.id)
        self.assertEqual((await self.channels.get_default(self.workspace.id)).name, "general")
        self.assertTrue(await self.channels.name_exists(self.workspace.id, "general"))
        self.assertFalse(await self.channels.name_exists(self.workspace.id, "general", exclude_channel_id=self.channel.id))
        channel = await self.channels.create(workspace_id=self.workspace.id, name="chat", type=ChannelType.TEXT)
        self.assertEqual(len(await self.channels.list_by_workspace(self.workspace.id)), 2)
        await self.channels.update(channel, name="renamed", description="Description", type=ChannelType.STUDY_ROOM)
        self.assertEqual(channel.type, ChannelType.STUDY_ROOM)
        insert = "INSERT INTO channels (id, workspace_id, name, type, is_default) VALUES (:id, :workspace, :name, :type, :default)"
        await self.rejected(insert, {"id": uuid4(), "workspace": self.workspace.id, "name": "general", "type": "TEXT", "default": False})
        await self.rejected(insert, {"id": uuid4(), "workspace": self.workspace.id, "name": "other", "type": "TEXT", "default": True})
        await self.rejected(insert, {"id": uuid4(), "workspace": uuid4(), "name": "orphan", "type": "TEXT", "default": False})

    async def test_message_attachment_reaction_repositories(self):
        now = datetime.now(UTC)
        message = await self.messages.create(channel_id=self.channel.id, sender_user_id=self.user.id, content=None)
        attachment = await self.attachments.create(
            message_id=message.id, storage_key="chat/object", original_filename="notes.pdf",
            content_type="application/pdf", size_bytes=1234,
        )
        await self.messages.update_content(message, content="Edited", edited_at=now)
        self.assertEqual((await self.messages.get_by_id(message.id, for_update=True)).content, "Edited")
        self.assertEqual((await self.messages.list_by_channel(self.channel.id))[0].id, message.id)
        self.assertEqual((await self.attachments.list_by_message(message.id))[0].id, attachment.id)
        first = await self.reactions.create(message_id=message.id, user_id=self.user.id, emoji="👍")
        second = await self.reactions.create(message_id=message.id, user_id=self.user.id, emoji="🎉")
        self.assertEqual((await self.reactions.find_exact(message.id, self.user.id, "👍")).id, first.id)
        self.assertEqual(await self.reactions.count_by_message(message.id), 2)
        self.assertEqual(len(await self.reactions.list_by_message(message.id)), 2)
        await self.rejected(
            "INSERT INTO message_reactions (id, message_id, user_id, emoji) VALUES (:id, :message, :user, :emoji)",
            {"id": uuid4(), "message": message.id, "user": self.user.id, "emoji": "👍"},
        )
        await self.messages.mark_deleted(message, deleted_at=now)
        self.assertEqual(message.deleted_at, now)
        await self.reactions.delete(second)
        self.assertEqual(await self.reactions.count_by_message(message.id), 1)

    async def test_cascade_cleanup_and_no_orphans(self):
        message = await self.messages.create(channel_id=self.channel.id, sender_user_id=self.user.id, content="Delete channel")
        attachment = await self.attachments.create(
            message_id=message.id, storage_key="key", original_filename="file", content_type="text/plain", size_bytes=1,
        )
        reaction = await self.reactions.create(message_id=message.id, user_id=self.user.id, emoji="✅")
        await self.channels.delete(self.channel)
        for model, identifier in ((ChatMessage, message.id), (ChatAttachment, attachment.id), (MessageReaction, reaction.id)):
            self.assertIsNone(await self.session.scalar(select(model).where(model.id == identifier)))
        await self.rejected(
            "INSERT INTO chat_attachments (id, message_id, storage_key, original_filename, content_type, size_bytes) VALUES (:id, :message, 'key', 'file', 'text/plain', 1)",
            {"id": uuid4(), "message": uuid4()},
        )

    async def test_schema_and_startup(self):
        def schema(connection):
            inspector = inspect(connection)
            return {
                table: (inspector.get_columns(table), inspector.get_indexes(table), inspector.get_unique_constraints(table), inspector.get_foreign_keys(table))
                for table in PHASE_3_TABLES
            }

        info = await self.connection.run_sync(schema)
        self.assertEqual({column["name"] for column in info["channels"][0]}, {"id", "workspace_id", "name", "description", "type", "is_default", "created_at", "updated_at"})
        self.assertTrue(any(index["name"] == "uq_channels_workspace_default" and index["unique"] for index in info["channels"][1]))
        self.assertTrue(any(index["name"] == "ix_chat_messages_channel_created_at" for index in info["chat_messages"][1]))
        for table, (columns, _, _, foreign_keys) in info.items():
            for column in columns:
                if column["name"].endswith("_at"):
                    self.assertTrue(column["type"].timezone)
            self.assertEqual(len(foreign_keys), {"channels": 1, "chat_messages": 2, "chat_attachments": 1, "message_reactions": 2}[table])

        from app.main import app
        async with app.router.lifespan_context(app):
            self.assertIsNotNone(app.openapi())
