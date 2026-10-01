"""Targeted Phase 4A tests, PostgreSQL fixtures rolled back after each test."""
import unittest
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi import WebSocketDisconnect

from app.api.v1.study_room import room_socket
from app.core.config import get_settings
from app.core.security import create_access_token
from app.realtime.study_room import RoomPresence
from tests import test_chat_realtime as fixtures
from tests.test_channel_chat_hardening import HttpAssertions

setUpModule = fixtures.setUpModule
tearDownModule = fixtures.tearDownModule


class StudyRoomTests(HttpAssertions, unittest.IsolatedAsyncioTestCase):
    asyncSetUp = fixtures.ChatRealtimeTests.asyncSetUp
    asyncTearDown = fixtures.ChatRealtimeTests.asyncTearDown

    async def test_media_token_authorization_grants_and_configuration(self):
        import jwt
        from pydantic import SecretStr
        settings = get_settings().model_copy(update={
            "livekit_url": "ws://localhost:7880", "livekit_api_key": SecretStr("test-api-key"),
            "livekit_api_secret": SecretStr("test-secret-for-media-token-only-123456789"),
        })
        async with self.client() as client:
            path = f"channels/{self.study_id}/study-room/media-token"
            with patch("app.core.config.get_settings", return_value=settings):
                response = await client.post(path, headers=self.headers(self.member), json={"user_id": str(self.outsider.user.id), "room_id": "untrusted-room"})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers["cache-control"], "no-store")
                data = response.json()["data"]
                claims = jwt.decode(data["token"], settings.livekit_api_secret.get_secret_value(), algorithms=["HS256"], issuer="test-api-key")
                self.assertEqual(claims["sub"], str(self.member.user.id))
                self.assertEqual(claims["video"]["room"], f"study-{self.study_id}")
                self.assertEqual(claims["video"]["canPublishSources"], ["microphone", "camera", "screen_share"])
                self.assertEqual(set(claims["video"]), {"roomJoin", "room", "canPublish", "canSubscribe", "canPublishData", "canPublishSources"})
                self.assertFalse(claims["video"]["canPublishData"])
                self.assertEqual(claims["exp"] - claims["nbf"], 300)
                self.assertNotIn(settings.livekit_api_secret.get_secret_value(), response.text)
                self.error(await client.post(path), 401, "AUTHENTICATION_REQUIRED")
                self.error(await client.post(path, headers=self.headers(self.outsider)), 403, "CHANNEL_PERMISSION_DENIED")
                self.error(await client.post(f"channels/{self.channel_id}/study-room/media-token", headers=self.headers(self.member)), 422, "CHANNEL_NOT_STUDY_ROOM")
                self.error(await client.post(f"channels/{uuid4()}/study-room/media-token", headers=self.headers(self.member)), 404, "CHANNEL_NOT_FOUND")
            with patch("app.core.config.get_settings", return_value=settings.model_copy(update={"livekit_api_secret": SecretStr("")})):
                self.error(await client.post(path, headers=self.headers(self.member)), 503, "MEDIA_NOT_CONFIGURED")

    async def test_room_http_member_outsider_anonymous_text_missing(self):
        async with self.client() as client:
            path = f"channels/{self.study_id}/study-room"
            response = await client.get(path, headers=self.headers(self.member))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["data"]["channel"]["type"], "STUDY_ROOM")
            self.assertEqual(response.json()["data"]["participants"], [])
            self.error(await client.get(path), 401, "AUTHENTICATION_REQUIRED")
            self.error(await client.get(path, headers=self.headers(self.outsider)), 403, "CHANNEL_PERMISSION_DENIED")
            self.error(await client.get(f"channels/{self.channel_id}/study-room", headers=self.headers(self.member)), 422, "CHANNEL_NOT_STUDY_ROOM")
            self.error(await client.get(f"channels/{uuid4()}/study-room", headers=self.headers(self.member)), 404, "CHANNEL_NOT_FOUND")

    async def socket(self, principal, actions, inspect=None, origin=None):
        test = self
        class Socket:
            headers = {"origin": origin or str(get_settings().frontend_url).rstrip("/")}
            frames = [{"type": "auth", "access_token": create_access_token(principal.user.id, principal.session.id)}, *(action if isinstance(action, dict) else {"type": action} for action in actions)]
            events = []
            code = None
            async def accept(self): pass
            async def close(self, code): self.code = code
            async def receive_json(self):
                if not self.frames: raise WebSocketDisconnect()
                return self.frames.pop(0)
            async def send_json(self, event):
                self.events.append(event["data"])
                if inspect: await inspect(event["data"])
        @asynccontextmanager
        async def db(): yield test.session
        socket = Socket()
        with patch("app.api.v1.study_room.session_factory", db):
            await room_socket(socket, self.study_id)
        return socket

    async def test_join_duplicate_leave_repeat_and_disconnect(self):
        presence = RoomPresence()
        with patch("app.api.v1.study_room.room_presence", presence):
            socket = await self.socket(self.member, ["join", "join", "leave", "leave", "join"])
        self.assertEqual([s["self_state"] for s in socket.events], ["LEFT", "IN_ROOM", "IN_ROOM", "LEFT", "LEFT", "IN_ROOM"])
        self.assertEqual(socket.events[1]["participants"], socket.events[2]["participants"])
        self.assertEqual(presence.snapshot(self.study_id)["participants"], [])

    async def test_two_members_observe_join_and_leave(self):
        presence = RoomPresence()
        observed = []
        async def observe(state):
            other = await self.socket(self.sender, [])
            observed.append(other.events[0]["participants"])
        with patch("app.api.v1.study_room.room_presence", presence):
            await self.socket(self.member, ["join", "leave"], observe)
        self.assertEqual([len(p) for p in observed], [0, 1, 0])

    async def test_devices_defaults_updates_observer_and_rejoin(self):
        presence = RoomPresence()
        observed = []
        async def observe(state):
            other = await self.socket(self.sender, ["join"])
            observed.append([p for p in other.events[-1]["participants"] if p["user_id"] == str(self.member.user.id)])
            async with self.client() as client:
                from app.schemas.study_room import RoomParticipant
                response = await client.get(f"channels/{self.study_id}/study-room", headers=self.headers(self.sender))
                self.assertEqual(response.json()["data"]["participants"], [RoomParticipant.model_validate(p).model_dump(mode="json") for p in state["participants"]])
        actions = ["join", {"type": "devices", "microphone_enabled": True},
                   {"type": "devices", "microphone_enabled": True},
                   {"type": "devices", "camera_enabled": True},
                   {"type": "devices", "microphone_enabled": False},
                   {"type": "devices", "camera_enabled": False},
                   {"type": "devices", "camera_enabled": True}, "leave", "join"]
        with patch("app.api.v1.study_room.room_presence", presence):
            socket = await self.socket(self.member, actions, observe)
        expected = [(False, False), (False, False), (True, False), (True, False),
                    (True, True), (False, True), (False, False), (False, True), (False, False), (False, False)]
        self.assertEqual([(s["self_devices"]["microphone_enabled"], s["self_devices"]["camera_enabled"]) for s in socket.events], expected)
        self.assertEqual(observed, [s["participants"] for s in socket.events])
        self.assertFalse(presence.connections)

    async def test_devices_require_participation_and_strict_boolean_payload(self):
        self.assertEqual((await self.socket(self.member, [{"type": "devices", "camera_enabled": True}])).code, 4403)
        self.assertEqual((await self.socket(self.outsider, [{"type": "devices", "camera_enabled": True}])).code, 4403)
        for fields in [{}, {"camera_enabled": "true"}, {"microphone_enabled": 1},
                       {"camera_enabled": True, "user_id": str(self.sender.user.id)}]:
            with self.subTest(fields=fields):
                socket = await self.socket(self.member, ["join", {"type": "devices", **fields}])
                self.assertEqual(socket.code, 1008)

    async def test_socket_outsider_origin_and_invalid_command(self):
        self.assertEqual((await self.socket(self.outsider, ["join"])).code, 4403)
        self.assertEqual((await self.socket(self.member, [], origin="https://invalid.example")).code, 1008)
        self.assertEqual((await self.socket(self.member, ["invalid"])).code, 1008)

    async def test_screen_share_state_snapshots_and_cleanup(self):
        presence = RoomPresence()
        observed = []
        async def observe(state):
            other = await self.socket(self.sender, [])
            observed.append(other.events[-1]["participants"])
        with patch("app.api.v1.study_room.room_presence", presence):
            socket = await self.socket(self.member, ["join", {"type": "devices", "screen_sharing": True},
                {"type": "devices", "screen_sharing": True}, {"type": "devices", "screen_sharing": False},
                {"type": "devices", "screen_sharing": True}, "leave", "join"], observe)
        self.assertEqual([s["self_devices"]["screen_sharing"] for s in socket.events], [False, False, True, True, False, True, False, False])
        self.assertEqual(observed, [s["participants"] for s in socket.events])
        self.assertFalse(presence.connections)

    async def test_screen_share_requires_join_and_strict_identity_free_payload(self):
        for principal in (self.member, self.outsider):
            self.assertEqual((await self.socket(principal, [{"type": "devices", "screen_sharing": True}])).code, 4403)
        for fields in ({"screen_sharing": 1}, {"screen_sharing": "true"}, {"screen_sharing": None},
                       {"screen_sharing": True, "user_id": str(self.sender.user.id)}):
            self.assertEqual((await self.socket(self.member, ["join", {"type": "devices", **fields}])).code, 1008)

    async def test_revoked_session_removed_on_next_frame(self):
        from datetime import UTC, datetime
        from app.models import AuthSession
        presence = RoomPresence()
        async def revoke(state):
            if state["self_state"] == "IN_ROOM":
                async with self.session.begin():
                    session = await self.session.get(AuthSession, self.member.session.id)
                    session.revoked_at = datetime.now(UTC)
        with patch("app.api.v1.study_room.room_presence", presence):
            socket = await self.socket(self.member, ["join", "state"], revoke)
        self.assertEqual(socket.code, 4401)
        self.assertFalse(presence.connections)

    async def test_removed_membership_evicts_participant(self):
        from sqlalchemy import delete
        from app.models import WorkspaceMember
        presence = RoomPresence()
        async def remove(state):
            if state["self_state"] == "IN_ROOM":
                async with self.session.begin():
                    await self.session.execute(delete(WorkspaceMember).where(WorkspaceMember.user_id == self.member.user.id))
        with patch("app.api.v1.study_room.room_presence", presence):
            socket = await self.socket(self.member, ["join", "state"], remove)
        self.assertEqual(socket.code, 4403)
        self.assertFalse(presence.connections)

    async def test_invalid_auth_and_timeout_leave_no_presence(self):
        @asynccontextmanager
        async def db(): yield self.session
        for frame, code in [({}, 4401), ({"type": "auth", "access_token": "invalid"}, 4401), (TimeoutError(), 4408), (ValueError(), 1008)]:
            with self.subTest(code=code):
                socket = AsyncMock()
                socket.headers = {"origin": str(get_settings().frontend_url)}
                if isinstance(frame, Exception): socket.receive_json.side_effect = frame
                else: socket.receive_json.return_value = frame
                presence = RoomPresence()
                with patch("app.api.v1.study_room.session_factory", db), patch("app.api.v1.study_room.room_presence", presence):
                    await room_socket(socket, self.study_id)
                socket.close.assert_awaited_once_with(code=code)
                self.assertFalse(presence.connections)


class PresenceTests(unittest.TestCase):
    def test_screen_share_ownership_and_simultaneous_participants(self):
        presence = RoomPresence(); room = uuid4()
        users = [SimpleNamespace(id=uuid4(), full_name=name) for name in ("A", "B")]
        for key, user in zip(("a", "b"), users):
            presence.update(key, room, user, "join")
            presence.update(key, room, user, "devices", {"screen_sharing": True})
        presence.update("a", room, users[0], "leave")
        self.assertTrue(presence.snapshot(room, "b")["self_devices"]["screen_sharing"])
        self.assertEqual(len(presence.snapshot(room)["participants"]), 1)
        presence.disconnect("b")
        self.assertEqual(presence.snapshot(room)["participants"], [])

    def test_tab_devices_aggregate_without_changing_other_tab_and_expiry_denies_update(self):
        from app.core.exceptions import AppError
        presence = RoomPresence()
        user = SimpleNamespace(id=uuid4(), full_name="Member")
        room = uuid4()
        with patch("app.realtime.study_room.monotonic", return_value=0):
            for key in ("a", "b"): presence.update(key, room, user, "join")
            presence.update("b", room, user, "devices", {"camera_enabled": True})
            snapshot = presence.snapshot(room, "a")
            self.assertFalse(snapshot["self_devices"]["camera_enabled"])
            self.assertTrue(snapshot["participants"][0]["camera_enabled"])
            presence.disconnect("b")
            self.assertFalse(presence.snapshot(room)["participants"][0]["camera_enabled"])
        with patch("app.realtime.study_room.monotonic", return_value=16):
            with self.assertRaises(AppError): presence.update("a", room, user, "devices", {"camera_enabled": True})
            presence.update("a", room, user, "join")
            self.assertFalse(presence.snapshot(room, "a")["self_devices"]["camera_enabled"])

    def test_multiple_tabs_and_expired_heartbeat(self):
        presence = RoomPresence()
        user = SimpleNamespace(id=uuid4(), full_name="Member")
        room = uuid4()
        with patch("app.realtime.study_room.monotonic", return_value=0):
            presence.update("a", room, user, "join")
            presence.update("b", room, user, "join")
            self.assertEqual(len(presence.snapshot(room)["participants"]), 1)
            presence.disconnect("a")
            self.assertEqual(len(presence.snapshot(room)["participants"]), 1)
        with patch("app.realtime.study_room.monotonic", return_value=16):
            self.assertEqual(presence.snapshot(room)["participants"], [])
