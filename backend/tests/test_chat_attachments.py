"""Phase 3B3 targeted attachment/storage verification."""
import os
import unittest
from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from sqlalchemy import func, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool
from starlette.datastructures import Headers, UploadFile

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.models import AuthSession, Channel, ChatAttachment, ChatMessage, User, Workspace, WorkspaceMember
from app.models.enums import ChannelType, WorkspaceRole
from app.services.auth_service import Principal
from app.services.chat_service import ChatService

BACKEND = Path(__file__).resolve().parents[1]
_original_url = None
_test_url = ""


def setUpModule():
    global _original_url, _test_url
    _test_url = os.environ.get("TEST_DATABASE_URL") or dotenv_values(BACKEND / ".env").get("TEST_DATABASE_URL") or ""
    url = make_url(_test_url)
    if url.database != "kltn_test" or url.drivername != "postgresql+asyncpg":
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


class FakeStorage:
    def __init__(self, *, fail_upload=False):
        self.fail_upload = fail_upload
        self.objects = {}
        self.deleted = []

    async def upload(self, key, body, content_type):
        if self.fail_upload:
            raise RuntimeError("storage unavailable")
        self.objects[key] = (body.read(), content_type)

    async def delete(self, key):
        self.deleted.append(key)
        self.objects.pop(key, None)

    async def temporary_download_url(self, key, filename):
        return f"http://storage.local/{key}?filename={filename}"


class RecordingManager:
    def __init__(self, session):
        self.session = session
        self.events = []

    async def broadcast(self, channel_id, event):
        self.events.append((channel_id, event, self.session.in_transaction()))


def upload(filename, content_type, data):
    return UploadFile(file=BytesIO(data), filename=filename, headers=Headers({"content-type": content_type}))


class ChatAttachmentTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine(_test_url, poolclass=NullPool)
        self.connection = await self.engine.connect()
        self.outer_transaction = await self.connection.begin()
        self.session = AsyncSession(bind=self.connection, expire_on_commit=False, join_transaction_mode="create_savepoint")
        users = [User(full_name=f"Attachment user {i}", email=f"{uuid4()}@example.com", password_hash="unused") for i in range(3)]
        workspace = Workspace(name="Attachment workspace")
        self.session.add_all([*users, workspace])
        await self.session.flush()
        sessions = [AuthSession(
            user_id=user.id, refresh_token_hash=uuid4().hex + uuid4().hex,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        ) for user in users]
        text = Channel(workspace_id=workspace.id, name="general", type=ChannelType.TEXT, is_default=True)
        study = Channel(workspace_id=workspace.id, name="study", type=ChannelType.STUDY_ROOM)
        self.session.add_all([
            *sessions, text, study,
            WorkspaceMember(workspace_id=workspace.id, user_id=users[0].id, role=WorkspaceRole.OWNER),
            WorkspaceMember(workspace_id=workspace.id, user_id=users[1].id, role=WorkspaceRole.MEMBER),
        ])
        await self.session.commit()
        self.text_id, self.study_id = text.id, study.id
        self.sender, self.member, self.outsider = [Principal(
            user=SimpleNamespace(id=user.id), session=SimpleNamespace(id=session.id),
        ) for user, session in zip(users, sessions)]
        self.storage = FakeStorage()
        self.manager = RecordingManager(self.session)
        self.chat = ChatService(self.session, manager=self.manager, storage=self.storage)

    async def asyncTearDown(self):
        await self.session.close()
        await self.outer_transaction.rollback()
        await self.connection.close()
        await self.engine.dispose()

    async def assert_error(self, code, awaitable):
        with self.assertRaises(AppError) as caught:
            await awaitable
        self.assertEqual(caught.exception.code, code)

    async def counts(self):
        async with self.session.begin():
            messages = await self.session.scalar(select(func.count()).select_from(ChatMessage))
            attachments = await self.session.scalar(select(func.count()).select_from(ChatAttachment))
        return messages, attachments

    async def test_upload_text_file_only_history_realtime_and_download(self):
        result = await self.chat.send_attachment(
            self.sender, self.text_id, upload("report.pdf", "application/pdf", b"%PDF-test"), " report ",
        )
        self.assertEqual(result.content, "report")
        self.assertEqual(result.attachments[0].original_filename, "report.pdf")
        self.assertNotIn("storage_key", result.model_dump())
        self.assertEqual(await self.counts(), (1, 1))
        self.assertEqual(len(self.storage.objects), 1)
        key = next(iter(self.storage.objects))
        self.assertNotIn("report.pdf", key)
        event = self.manager.events[-1]
        self.assertEqual(event[1]["type"], "message.created")
        self.assertEqual(event[1]["data"]["attachments"][0]["size_bytes"], 9)
        self.assertFalse(event[2])
        history = await self.chat.history(self.member, self.text_id, limit=10, before_message_id=None)
        self.assertEqual(history[0].attachments[0].id, result.attachments[0].id)
        url = await self.chat.attachment_download_url(self.member, result.attachments[0].id)
        self.assertIn(key, url)

        file_only = await self.chat.send_attachment(
            self.sender, self.text_id, upload("note.txt", "text/plain", b"note"), None,
        )
        self.assertIsNone(file_only.content)

    async def test_file_policy_access_channel_and_deleted_message(self):
        await self.assert_error("ATTACHMENT_EMPTY", self.chat.send_attachment(
            self.sender, self.text_id, upload("empty.txt", "text/plain", b""), None,
        ))
        await self.assert_error("ATTACHMENT_TYPE_NOT_ALLOWED", self.chat.send_attachment(
            self.sender, self.text_id, upload("script.exe", "application/octet-stream", b"MZ"), None,
        ))
        oversized = b"x" * (get_settings().attachment_max_size_bytes + 1)
        await self.assert_error("ATTACHMENT_TOO_LARGE", self.chat.send_attachment(
            self.sender, self.text_id, upload("large.txt", "text/plain", oversized), None,
        ))
        await self.assert_error("CHANNEL_ACCESS_DENIED", self.chat.send_attachment(
            self.outsider, self.text_id, upload("note.txt", "text/plain", b"note"), None,
        ))
        await self.assert_error("CHANNEL_NOT_TEXT", self.chat.send_attachment(
            self.sender, self.study_id, upload("note.txt", "text/plain", b"note"), None,
        ))
        created = await self.chat.send_attachment(
            self.sender, self.text_id, upload("note.txt", "text/plain", b"note"), None,
        )
        await self.assert_error(
            "ATTACHMENT_ACCESS_DENIED",
            self.chat.attachment_download_url(self.outsider, created.attachments[0].id),
        )
        await self.chat.delete(self.sender, created.id)
        await self.assert_error(
            "ATTACHMENT_NOT_FOUND", self.chat.attachment_download_url(self.sender, created.attachments[0].id),
        )

    async def test_storage_and_database_failure_consistency(self):
        failing = ChatService(self.session, manager=self.manager, storage=FakeStorage(fail_upload=True))
        await self.assert_error("ATTACHMENT_UPLOAD_FAILED", failing.send_attachment(
            self.sender, self.text_id, upload("note.txt", "text/plain", b"note"), None,
        ))
        self.assertEqual(await self.counts(), (0, 0))

        async def fail_create(**kwargs):
            raise RuntimeError("database failure")

        self.chat.attachments.create = fail_create
        with self.assertRaises(RuntimeError):
            await self.chat.send_attachment(
                self.sender, self.text_id, upload("note.txt", "text/plain", b"note"), None,
            )
        self.assertEqual(await self.counts(), (0, 0))
        self.assertEqual(len(self.storage.deleted), 1)
        self.assertEqual(self.storage.objects, {})

    async def test_routes_and_startup(self):
        from app.main import app

        expected = {
            ("POST", "/api/v1/channels/{channel_id}/messages/attachments"),
            ("GET", "/api/v1/attachments/{attachment_id}/download"),
        }
        async with app.router.lifespan_context(app):
            routes = {
                (method.upper(), path)
                for path, operations in app.openapi()["paths"].items()
                for method in operations
            }
        self.assertTrue(expected <= routes, expected - routes)
