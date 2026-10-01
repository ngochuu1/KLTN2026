"""Phase 3C HTTP/transaction coverage using the existing PostgreSQL fixtures."""
import unittest
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import httpx
from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import create_access_token
from app.models import ChatMessage, MessageReaction
from app.schemas.chat import MessageRequest
from tests import test_chat_realtime as realtime
from tests import test_chat_attachments as attachments


def setUpModule():
    realtime.setUpModule()
    attachments._test_url = realtime._test_url


def tearDownModule():
    realtime.tearDownModule()


class HttpAssertions:
    @asynccontextmanager
    async def client(self):
        from app.main import app
        from app.db.session import get_db

        async def db():
            yield self.session

        previous = app.dependency_overrides.copy()
        app.dependency_overrides[get_db] = db
        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://testserver/api/v1/",
            ) as client:
                yield client
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous)

    def headers(self, principal):
        return {"Authorization": "Bearer " + create_access_token(principal.user.id, principal.session.id)}

    def error(self, response, status, code):
        self.assertEqual(response.status_code, status, response.text)
        self.assertEqual(set(response.json()), {"error"})
        self.assertEqual(set(response.json()["error"]), {"code", "message", "fields"})
        self.assertEqual(response.json()["error"]["code"], code)


class ChatCorsTests(unittest.IsolatedAsyncioTestCase):
    async def test_uvicorn_runtime_has_websocket_transport(self):
        from uvicorn import Config
        from app.main import app

        config = Config(app, ws="auto", log_config=None)
        config.load()
        self.assertIsNotNone(config.ws_protocol_class, "Install a WebSocket transport for the deployed Uvicorn runtime")

    async def test_browser_reaction_preflight_allows_put_only_for_frontend(self):
        from app.main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
            headers = {
                "Origin": str(get_settings().frontend_url).rstrip("/"),
                "Access-Control-Request-Method": "PUT",
                "Access-Control-Request-Headers": "authorization",
            }
            response = await client.options(f"/api/v1/messages/{uuid4()}/reactions/like", headers=headers)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.headers["access-control-allow-origin"], headers["Origin"])
            self.assertIn("PUT", response.headers["access-control-allow-methods"])
            headers["Origin"] = "https://untrusted.example"
            response = await client.options(f"/api/v1/messages/{uuid4()}/reactions/like", headers=headers)
            self.assertEqual(response.status_code, 400)
            self.assertNotIn("access-control-allow-origin", response.headers)


class ChatHttpTests(HttpAssertions, unittest.IsolatedAsyncioTestCase):
    asyncSetUp = realtime.ChatRealtimeTests.asyncSetUp
    asyncTearDown = realtime.ChatRealtimeTests.asyncTearDown

    async def test_message_http_persistence_events_and_soft_delete(self):
        with patch("app.api.v1.chat.ChatService", return_value=self.chat):
            async with self.client() as client:
                client.headers.update(self.headers(self.sender))
                response = await client.post(f"channels/{self.channel_id}/messages", json={"content": " hello "})
                self.assertEqual(response.status_code, 201, response.text)
                data = response.json()["data"]
                mid = UUID(data["id"])
                self.assertEqual(self.manager.events[-1], (self.channel_id, {"type": "message.created", "data": data}))
                async with self.session.begin():
                    row = await self.session.get(ChatMessage, mid, populate_existing=True)
                    self.assertEqual((row.content, row.sender_user_id), ("hello", self.sender.user.id))
                response = await client.patch(f"messages/{mid}", json={"content": "edited"})
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(self.manager.events[-1][1], {"type": "message.updated", "data": response.json()["data"]})
                history = await client.get(f"channels/{self.channel_id}/messages")
                self.assertEqual(history.json()["data"], [response.json()["data"]])
                response = await client.delete(f"messages/{mid}")
                self.assertEqual((response.status_code, response.content), (204, b""))
                async with self.session.begin():
                    row = await self.session.get(ChatMessage, mid, populate_existing=True)
                    self.assertIsNotNone(row.deleted_at)
                    self.assertEqual(row.content, "edited")
                self.assertEqual(self.manager.events[-1][1], {"type": "message.deleted", "data": {"message_id": str(mid)}})
                self.assertFalse(any(self.manager.broadcast_during_transaction))

    async def test_message_errors_do_not_mutate_or_broadcast(self):
        message = await self.chat.send(self.sender, self.channel_id, MessageRequest(content="original"))
        count = len(self.manager.events)
        with patch("app.api.v1.chat.ChatService", return_value=self.chat):
            async with self.client() as client:
                for principal, status, code in [(self.member, 403, "MESSAGE_PERMISSION_DENIED"), (self.outsider, 403, "CHANNEL_ACCESS_DENIED")]:
                    for method in ("PATCH", "DELETE"):
                        kwargs = {"json": {"content": "denied"}} if method == "PATCH" else {}
                        self.error(await client.request(method, f"messages/{message.id}", headers=self.headers(principal), **kwargs), status, code)
                client.headers.update(self.headers(self.sender))
                for content in (None, "", " \n "):
                    self.error(await client.post(f"channels/{self.channel_id}/messages", json={"content": content}), 422, "INVALID_MESSAGE_CONTENT")
                    self.error(await client.patch(f"messages/{message.id}", json={"content": content}), 422, "INVALID_MESSAGE_CONTENT")
                for method, path, kwargs, code in [
                    ("POST", f"channels/{uuid4()}/messages", {"json": {"content": "valid"}}, "CHANNEL_NOT_FOUND"),
                    ("PATCH", f"messages/{uuid4()}", {"json": {"content": "valid"}}, "MESSAGE_NOT_FOUND"),
                    ("DELETE", f"messages/{uuid4()}", {}, "MESSAGE_NOT_FOUND"),
                    ("GET", f"channels/{self.channel_id}/messages?before_message_id={uuid4()}", {}, "MESSAGE_NOT_FOUND"),
                ]:
                    self.error(await client.request(method, path, **kwargs), 404, code)
                self.error(await client.get(f"channels/{self.channel_id}/messages?limit=0"), 422, "VALIDATION_ERROR")
                self.error(await client.post(f"channels/{self.channel_id}/messages", json={"content": "x"}, headers=self.headers(self.outsider)), 403, "CHANNEL_ACCESS_DENIED")
        self.assertEqual(len(self.manager.events), count)
        self.assertEqual((await self.chat.history(self.sender, self.channel_id, limit=10, before_message_id=None))[0].content, "original")

    async def test_reaction_http_ownership_persistence_and_exact_events(self):
        message = await self.chat.send(self.sender, self.channel_id, MessageRequest(content="reactions"))
        path = f"messages/{message.id}/reactions/like"
        with patch("app.api.v1.chat.ChatService", return_value=self.chat):
            async with self.client() as client:
                for principal in (self.sender, self.member):
                    response = await client.put(path, headers=self.headers(principal))
                    self.assertEqual(response.status_code, 200, response.text)
                expected = [{"emoji": "like", "count": 2}]
                self.assertEqual(response.json()["data"], expected)
                self.assertEqual(self.manager.events[-1][1], {"type": "reaction.updated", "data": {"message_id": str(message.id), "reactions": expected}})
                count = len(self.manager.events)
                await client.put(path, headers=self.headers(self.member))
                self.assertEqual(len(self.manager.events), count)
                for method in ("PUT", "DELETE"):
                    self.error(await client.request(method, path, headers=self.headers(self.outsider)), 403, "CHANNEL_ACCESS_DENIED")
                response = await client.delete(path, headers=self.headers(self.member))
                self.assertEqual((response.status_code, response.content), (204, b""))
                count = len(self.manager.events)
                await client.delete(path, headers=self.headers(self.member))
                self.assertEqual(len(self.manager.events), count)
                async with self.session.begin():
                    rows = (await self.session.scalars(select(MessageReaction).where(MessageReaction.message_id == message.id))).all()
                    self.assertEqual([(r.user_id, r.emoji) for r in rows], [(self.sender.user.id, "like")])
                self.assertFalse(any(self.manager.broadcast_during_transaction))

    async def test_failed_message_transaction_has_no_row_or_event(self):
        with patch.object(self.chat.messages, "get_with_details", new=AsyncMock(side_effect=RuntimeError("database failure"))):
            with self.assertRaisesRegex(RuntimeError, "database failure"):
                await self.chat.send(self.sender, self.channel_id, MessageRequest(content="rollback"))
        self.assertEqual(self.manager.events, [])
        self.assertEqual(await self.chat.history(self.sender, self.channel_id, limit=10, before_message_id=None), [])


class AttachmentHttpTests(HttpAssertions, unittest.IsolatedAsyncioTestCase):
    asyncSetUp = attachments.ChatAttachmentTests.asyncSetUp
    asyncTearDown = attachments.ChatAttachmentTests.asyncTearDown
    counts = attachments.ChatAttachmentTests.counts

    async def test_upload_download_http_and_no_unauthorized_signing(self):
        self.storage.temporary_download_url = AsyncMock(return_value="http://storage.local/private")
        with patch("app.api.v1.chat.ChatService", return_value=self.chat):
            async with self.client() as client:
                response = await client.post(f"channels/{self.text_id}/messages/attachments", headers=self.headers(self.sender), files={"file": ("note.txt", b"hello", "text/plain")})
                self.assertEqual(response.status_code, 201, response.text)
                data = response.json()["data"]
                attachment = data["attachments"][0]
                self.assertEqual(set(attachment), {"id", "original_filename", "content_type", "size_bytes"})
                self.assertEqual(self.manager.events[-1][1], {"type": "message.created", "data": data})
                path = f"attachments/{attachment['id']}/download"
                self.error(await client.get(path), 401, "AUTHENTICATION_REQUIRED")
                self.error(await client.get(path, headers=self.headers(self.outsider)), 403, "ATTACHMENT_ACCESS_DENIED")
                self.storage.temporary_download_url.assert_not_awaited()
                response = await client.get(path, headers=self.headers(self.member))
                self.assertEqual(response.status_code, 307)
                self.assertEqual(response.headers["location"], "http://storage.local/private")
                self.storage.temporary_download_url.assert_awaited_once_with(next(iter(self.storage.objects)), "note.txt")
                self.assertEqual(await self.counts(), (1, 1))

    async def test_exact_25mb_boundary_and_rejected_upload_side_effects(self):
        maximum = get_settings().attachment_max_size_bytes
        self.assertEqual(maximum, 25 * 1024 * 1024)
        result = await self.chat.send_attachment(self.sender, self.text_id, attachments.upload("limit.txt", "text/plain", b"x" * maximum), None)
        self.assertEqual(result.attachments[0].size_bytes, maximum)
        with patch("app.api.v1.chat.ChatService", return_value=self.chat):
            async with self.client() as client:
                cases = [(self.sender, self.text_id, b"x" * (maximum + 1), 413, "ATTACHMENT_TOO_LARGE"), (self.outsider, self.text_id, b"x", 403, "CHANNEL_ACCESS_DENIED"), (self.sender, self.study_id, b"x", 422, "CHANNEL_NOT_TEXT")]
                for principal, channel, body, status, code in cases:
                    self.error(await client.post(f"channels/{channel}/messages/attachments", headers=self.headers(principal), files={"file": ("file.txt", body, "text/plain")}), status, code)
        self.assertEqual(await self.counts(), (1, 1))
        self.assertEqual(len(self.storage.objects), 1)
        self.assertEqual(len(self.manager.events), 1)

    async def test_missing_storage_config_rejected_before_client_creation(self):
        from app.services.storage_service import get_storage_service
        from pydantic import SecretStr

        settings = get_settings()
        for field in ("object_storage_endpoint", "object_storage_access_key", "object_storage_secret_key", "object_storage_bucket"):
            with self.subTest(field=field):
                value = SecretStr("") if field.endswith("key") else ""
                with patch("app.services.storage_service.get_settings", return_value=settings.model_copy(update={field: value})), patch("app.services.storage_service.boto3.client") as factory:
                    with self.assertRaisesRegex(RuntimeError, "Object storage environment variables are required"):
                        get_storage_service.__wrapped__()
                    factory.assert_not_called()


class ChannelHttpTests(HttpAssertions, unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        from tests import test_channel_backend as channels
        channels._test_url = realtime._test_url
        await channels.ChannelBackendTests.asyncSetUp(self)

    asyncTearDown = realtime.ChatRealtimeTests.asyncTearDown

    async def test_channel_http_roles_validation_missing_and_duplicate_rollback(self):
        async with self.client() as client:
            base = f"workspaces/{self.workspace_id}/channels"
            self.error(await client.get(base), 401, "AUTHENTICATION_REQUIRED")
            client.headers.update(self.headers(self.owner))
            response = await client.post(base, json={"name": "new", "type": "TEXT"})
            self.assertEqual(response.status_code, 201, response.text)
            cid = response.json()["data"]["id"]
            for principal in (self.member, self.outsider):
                headers = self.headers(principal)
                self.error(await client.post(base, json={"name": "denied", "type": "TEXT"}, headers=headers), 403, "CHANNEL_PERMISSION_DENIED")
                self.error(await client.patch(f"channels/{cid}", json={"name": "denied"}, headers=headers), 403, "CHANNEL_PERMISSION_DENIED")
                self.error(await client.delete(f"channels/{cid}", headers=headers), 403, "CHANNEL_PERMISSION_DENIED")
            self.error(await client.get(base, headers=self.headers(self.outsider)), 403, "CHANNEL_PERMISSION_DENIED")
            self.error(await client.post(base, json={"name": "new", "type": "TEXT"}), 409, "CHANNEL_NAME_ALREADY_EXISTS")
            self.error(await client.patch(f"channels/{cid}", json={"name": "general"}), 409, "CHANNEL_NAME_ALREADY_EXISTS")
            self.assertEqual((await client.get(f"channels/{cid}")).json()["data"]["name"], "new")
            self.error(await client.post(base, json={"name": "bad", "type": "VOICE"}), 422, "INVALID_CHANNEL_TYPE")
            for payload in ({}, {"name": None}, {"name": " "}, {"type": "TEXT"}):
                self.error(await client.patch(f"channels/{cid}", json=payload), 422, "VALIDATION_ERROR")
            listed = await client.get(base, headers=self.headers(self.member))
            self.assertEqual(listed.status_code, 200)
            general = next(c for c in listed.json()["data"] if c["is_default"])
            self.assertEqual((general["name"], general["type"]), ("general", "TEXT"))
            for principal in (self.owner, self.admin):
                self.error(await client.delete(f"channels/{general['id']}", headers=self.headers(principal)), 403, "DEFAULT_CHANNEL_CANNOT_BE_DELETED")
            response = await client.patch(f"channels/{cid}", json={"description": "admin edit"}, headers=self.headers(self.admin))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["data"]["description"], "admin edit")
            response = await client.delete(f"channels/{cid}", headers=self.headers(self.admin))
            self.assertEqual((response.status_code, response.content), (204, b""))
            self.error(await client.get(f"channels/{cid}"), 404, "CHANNEL_NOT_FOUND")
            missing = uuid4()
            for method, path, kwargs, code in [
                ("GET", f"workspaces/{missing}/channels", {}, "WORKSPACE_NOT_FOUND"),
                ("POST", f"workspaces/{missing}/channels", {"json": {"name": "missing", "type": "TEXT"}}, "WORKSPACE_NOT_FOUND"),
                ("GET", f"channels/{missing}", {}, "CHANNEL_NOT_FOUND"),
                ("PATCH", f"channels/{missing}", {"json": {"name": "missing"}}, "CHANNEL_NOT_FOUND"),
                ("DELETE", f"channels/{missing}", {}, "CHANNEL_NOT_FOUND"),
            ]:
                self.error(await client.request(method, path, **kwargs), 404, code)


class WebSocketTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp = realtime.ChatRealtimeTests.asyncSetUp
    asyncTearDown = realtime.ChatRealtimeTests.asyncTearDown

    async def test_auth_frames_authorization_timeout_and_cleanup(self):
        from app.api.v1 import chat_websocket as ws
        from starlette.websockets import WebSocketDisconnect

        @asynccontextmanager
        async def db():
            yield self.session

        token = create_access_token(self.sender.user.id, self.sender.session.id)
        outsider = create_access_token(self.outsider.user.id, self.outsider.session.id)
        cases = [
            (self.channel_id, {}, 4401),
            (self.channel_id, {"type": "auth", "access_token": "invalid"}, 4401),
            (self.channel_id, {"type": "auth", "access_token": outsider}, 4403),
            (uuid4(), {"type": "auth", "access_token": token}, 4404),
            (self.channel_id, {"type": "auth", "access_token": token}, None),
            (self.channel_id, TimeoutError(), 4408),
            (self.channel_id, ValueError("invalid JSON"), 4401),
        ]
        for channel, frame, code in cases:
            with self.subTest(code=code, frame_type=type(frame).__name__):
                socket = AsyncMock()
                socket.headers = {"origin": str(get_settings().frontend_url)}
                if isinstance(frame, Exception):
                    socket.receive_json.side_effect = frame
                else:
                    socket.receive_json.return_value = frame
                socket.receive_text.side_effect = WebSocketDisconnect()
                manager = realtime.ChannelConnectionManager()
                with patch.object(ws, "session_factory", db), patch.object(ws, "channel_connections", manager):
                    await ws.channel_socket(socket, channel)
                socket.accept.assert_awaited_once()
                if code:
                    socket.close.assert_awaited_once_with(code=code)
                    socket.receive_text.assert_not_awaited()
                else:
                    socket.close.assert_not_awaited()
                    socket.receive_text.assert_awaited_once()
                self.assertEqual(manager.connection_count(channel), 0)
        socket = AsyncMock()
        socket.headers = {"origin": "https://invalid.example"}
        await ws.channel_socket(socket, self.channel_id)
        socket.close.assert_awaited_once_with(code=1008)
        socket.accept.assert_not_awaited()
