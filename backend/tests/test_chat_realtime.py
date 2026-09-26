"""Phase 3B2 targeted PostgreSQL and realtime verification."""
import os
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from sqlalchemy import func, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.security import create_access_token
from app.models import AuthSession, Channel, MessageReaction, User, Workspace, WorkspaceMember
from app.models.enums import ChannelType, WorkspaceRole
from app.realtime.connection_manager import ChannelConnectionManager
from app.schemas.chat import MessageRequest
from app.services.auth_service import Principal
from app.services.chat_service import ChatService

BACKEND = Path(__file__).resolve().parents[1]
_original_url = None
_test_url = ""


def setUpModule():
    global _original_url, _test_url
    _test_url = os.environ.get("TEST_DATABASE_URL") or dotenv_values(BACKEND / ".env").get("TEST_DATABASE_URL") or ""
    url = make_url(_test_url)
    if url.database != "kltn_test" or url.drivername != "postgresql+asyncpg" or url.database == make_url(str(get_settings().database_url)).database:
        raise RuntimeError("Requires dedicated kltn_test PostgreSQL database")
    _original_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = _test_url
    get_settings.cache_clear()
    config = Config(str(BACKEND / "alembic.ini"))
    command.upgrade(config, "head")
    command.check(config)


def tearDownModule():
    if _original_url is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = _original_url
    get_settings.cache_clear()


class RecordingManager:
    def __init__(self, session):
        self.session = session
        self.events = []
        self.broadcast_during_transaction = []

    async def broadcast(self, channel_id, event):
        self.broadcast_during_transaction.append(self.session.in_transaction())
        self.events.append((channel_id, event))


class FakeSocket:
    def __init__(self, *, fail=False):
        self.fail = fail
        self.events = []

    async def send_json(self, event):
        if self.fail:
            raise RuntimeError("disconnected")
        self.events.append(event)


class ChatRealtimeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine(_test_url, poolclass=NullPool)
        self.connection = await self.engine.connect()
        self.outer_transaction = await self.connection.begin()
        self.session = AsyncSession(bind=self.connection, expire_on_commit=False, join_transaction_mode="create_savepoint")
        users = [User(full_name=f"Chat user {index}", email=f"{uuid4()}@example.com", password_hash="unused") for index in range(3)]
        workspace = Workspace(name="Realtime workspace")
        self.session.add_all([*users, workspace])
        await self.session.flush()
        sessions = [AuthSession(
            user_id=user.id, refresh_token_hash=uuid4().hex + uuid4().hex,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        ) for user in users]
        channel = Channel(workspace_id=workspace.id, name="general", type=ChannelType.TEXT, is_default=True)
        study = Channel(workspace_id=workspace.id, name="study", type=ChannelType.STUDY_ROOM)
        self.session.add_all([
            *sessions, channel, study,
            WorkspaceMember(workspace_id=workspace.id, user_id=users[0].id, role=WorkspaceRole.OWNER),
            WorkspaceMember(workspace_id=workspace.id, user_id=users[1].id, role=WorkspaceRole.MEMBER),
        ])
        await self.session.commit()
        self.channel_id = channel.id
        self.study_id = study.id
        self.principals = [Principal(
            user=SimpleNamespace(id=user.id), session=SimpleNamespace(id=session.id),
        ) for user, session in zip(users, sessions)]
        self.sender, self.member, self.outsider = self.principals
        self.manager = RecordingManager(self.session)
        self.chat = ChatService(self.session, manager=self.manager)

    async def asyncTearDown(self):
        await self.session.close()
        await self.outer_transaction.rollback()
        await self.connection.close()
        await self.engine.dispose()

    async def assert_app_error(self, code, awaitable):
        with self.assertRaises(AppError) as caught:
            await awaitable
        self.assertEqual(caught.exception.code, code)

    async def test_history_access_pagination_and_text_only(self):
        first = await self.chat.send(self.sender, self.channel_id, MessageRequest(content="first"))
        second = await self.chat.send(self.sender, self.channel_id, MessageRequest(content="second"))
        ordered = await self.chat.history(self.member, self.channel_id, limit=10, before_message_id=None)
        self.assertEqual({item.id for item in ordered}, {first.id, second.id})
        history = await self.chat.history(self.member, self.channel_id, limit=1, before_message_id=None)
        self.assertEqual([item.id for item in history], [ordered[0].id])
        older = await self.chat.history(self.member, self.channel_id, limit=10, before_message_id=ordered[0].id)
        self.assertEqual([item.id for item in older], [ordered[1].id])
        await self.assert_app_error(
            "CHANNEL_ACCESS_DENIED", self.chat.history(self.outsider, self.channel_id, limit=50, before_message_id=None),
        )
        await self.assert_app_error(
            "CHANNEL_NOT_TEXT", self.chat.send(self.sender, self.study_id, MessageRequest(content="not allowed")),
        )

    async def test_send_edit_delete_persist_and_broadcast_after_commit(self):
        await self.assert_app_error(
            "INVALID_MESSAGE_CONTENT", self.chat.send(self.sender, self.channel_id, MessageRequest(content="   ")),
        )
        created = await self.chat.send(self.sender, self.channel_id, MessageRequest(content=" hello "))
        self.assertEqual(created.content, "hello")
        self.assertEqual(self.manager.events[-1][1]["type"], "message.created")
        self.assertFalse(self.manager.broadcast_during_transaction[-1])
        await self.assert_app_error(
            "MESSAGE_PERMISSION_DENIED", self.chat.edit(self.member, created.id, MessageRequest(content="denied")),
        )
        edited = await self.chat.edit(self.sender, created.id, MessageRequest(content="edited"))
        self.assertIsNotNone(edited.edited_at)
        self.assertEqual(self.manager.events[-1][1]["type"], "message.updated")
        await self.assert_app_error("MESSAGE_PERMISSION_DENIED", self.chat.delete(self.member, created.id))
        await self.chat.delete(self.sender, created.id)
        self.assertEqual(self.manager.events[-1][1], {
            "type": "message.deleted", "data": {"message_id": str(created.id)},
        })
        self.assertEqual(await self.chat.history(self.member, self.channel_id, limit=50, before_message_id=None), [])
        await self.assert_app_error("MESSAGE_ALREADY_DELETED", self.chat.delete(self.sender, created.id))

    async def test_reaction_idempotence_multiple_and_deleted_denial(self):
        message = await self.chat.send(self.sender, self.channel_id, MessageRequest(content="react"))
        await self.chat.add_reaction(self.member, message.id, "👍")
        self.assertEqual(self.manager.events[-1][1]["type"], "reaction.updated")
        event_count = len(self.manager.events)
        await self.chat.add_reaction(self.member, message.id, "👍")
        self.assertEqual(len(self.manager.events), event_count)
        await self.chat.add_reaction(self.member, message.id, "🎉")
        async with self.session.begin():
            count = await self.session.scalar(select(func.count()).select_from(MessageReaction).where(
                MessageReaction.message_id == message.id, MessageReaction.user_id == self.member.user.id,
            ))
        self.assertEqual(count, 2)
        await self.chat.remove_reaction(self.member, message.id, "👍")
        self.assertEqual(self.manager.events[-1][1]["type"], "reaction.updated")
        await self.chat.delete(self.sender, message.id)
        await self.assert_app_error("MESSAGE_ALREADY_DELETED", self.chat.add_reaction(self.member, message.id, "✅"))

    async def test_websocket_auth_membership_and_connection_cleanup(self):
        from app.api.v1.chat_websocket import authenticate_channel, origin_allowed, router

        token = create_access_token(self.sender.user.id, self.sender.session.id)
        outsider_token = create_access_token(self.outsider.user.id, self.outsider.session.id)
        authenticated = await authenticate_channel(self.session, self.channel_id, token)
        self.assertEqual(authenticated.user.id, self.sender.user.id)
        await self.assert_app_error("CHANNEL_ACCESS_DENIED", authenticate_channel(self.session, self.channel_id, outsider_token))
        await self.assert_app_error("ACCESS_TOKEN_INVALID", authenticate_channel(self.session, self.channel_id, "invalid"))
        self.assertTrue(origin_allowed(str(get_settings().frontend_url)))
        self.assertFalse(origin_allowed("https://invalid.example"))
        self.assertTrue(any(getattr(route, "path", None) == "/ws/channels/{channel_id}" for route in router.routes))

        manager = ChannelConnectionManager()
        live, dead = FakeSocket(), FakeSocket(fail=True)
        await manager.connect(self.channel_id, live)
        await manager.connect(self.channel_id, dead)
        await manager.broadcast(self.channel_id, {"type": "message.created", "data": {}})
        self.assertEqual(live.events[0]["type"], "message.created")
        self.assertEqual(manager.connection_count(self.channel_id), 1)
        manager.disconnect(self.channel_id, live)
        self.assertEqual(manager.connection_count(self.channel_id), 0)

    async def test_rest_routes_events_and_backend_startup(self):
        from app.main import app

        expected = {
            ("GET", "/api/v1/channels/{channel_id}/messages"),
            ("POST", "/api/v1/channels/{channel_id}/messages"),
            ("PATCH", "/api/v1/messages/{message_id}"),
            ("DELETE", "/api/v1/messages/{message_id}"),
            ("PUT", "/api/v1/messages/{message_id}/reactions/{emoji}"),
            ("DELETE", "/api/v1/messages/{message_id}/reactions/{emoji}"),
        }
        async with app.router.lifespan_context(app):
            schema = app.openapi()
            routes = {(method.upper(), path) for path, operations in schema["paths"].items() for method in operations}
            self.assertTrue(expected <= routes, expected - routes)
        await self.chat.send(self.sender, self.channel_id, MessageRequest(content="events"))
        message_id = UUID(self.manager.events[-1][1]["data"]["id"])
        await self.chat.edit(self.sender, message_id, MessageRequest(content="updated"))
        await self.chat.add_reaction(self.sender, message_id, "👍")
        await self.chat.delete(self.sender, message_id)
        self.assertEqual(
            {event["type"] for _, event in self.manager.events},
            {"message.created", "message.updated", "message.deleted", "reaction.updated"},
        )
