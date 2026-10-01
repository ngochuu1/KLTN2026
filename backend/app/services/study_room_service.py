from app.core.exceptions import AppError
from app.models.enums import ChannelType
from app.services.channel_service import ChannelService


class StudyRoomService(ChannelService):
    async def media_token(self, principal, channel_id):
        from datetime import UTC, datetime, timedelta
        import jwt
        from app.core.config import get_settings

        await self.authorize(principal, channel_id)
        settings = get_settings()
        key = settings.livekit_api_key.get_secret_value()
        secret = settings.livekit_api_secret.get_secret_value()
        if not settings.livekit_url.startswith(("ws://", "wss://")) or not key or len(secret) < 32:
            raise AppError(503, "MEDIA_NOT_CONFIGURED", "Máy chủ media chưa được cấu hình")
        now = datetime.now(UTC)
        room = f"study-{channel_id}"
        identity = str(principal.user.id)
        token = jwt.encode({
            "iss": key, "sub": identity, "name": principal.user.full_name,
            "nbf": now, "exp": now + timedelta(minutes=5),
            "video": {"roomJoin": True, "room": room, "canPublish": True,
                      "canSubscribe": True, "canPublishData": False,
                      "canPublishSources": ["microphone", "camera", "screen_share"]},
        }, secret, algorithm="HS256")
        return {"url": settings.livekit_url, "token": token, "room": room, "identity": identity}

    async def authorize(self, principal, channel_id):
        async with self.transaction(principal):
            channel = await self.channel_access(channel_id, principal.user.id)
            if channel.type != ChannelType.STUDY_ROOM:
                raise AppError(422, "CHANNEL_NOT_STUDY_ROOM", "Channel không phải phòng tự học")
            return self.response(channel)
