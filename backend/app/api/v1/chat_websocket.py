import asyncio
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.db.session import session_factory
from app.realtime.connection_manager import channel_connections
from app.services.auth_service import AuthService
from app.services.chat_service import ChatService

router = APIRouter(tags=["chat"])
AUTH_TIMEOUT_SECONDS = 5


async def authenticate_channel(db, channel_id: UUID, access_token: str):
    principal = await AuthService(db).authenticate(access_token)
    await ChatService(db).authorize_subscription(principal, channel_id)
    return principal


def origin_allowed(origin: str | None) -> bool:
    expected = str(get_settings().frontend_url).rstrip("/")
    return origin is not None and origin.rstrip("/") == expected


@router.websocket("/ws/channels/{channel_id}")
async def channel_socket(websocket: WebSocket, channel_id: UUID):
    if not origin_allowed(websocket.headers.get("origin")):
        await websocket.close(code=1008)
        return
    await websocket.accept()
    registered = False
    try:
        try:
            frame = await asyncio.wait_for(websocket.receive_json(), timeout=AUTH_TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            await websocket.close(code=4408)
            return
        except (TypeError, ValueError):
            await websocket.close(code=4401)
            return
        if not isinstance(frame, dict) or frame.get("type") != "auth" or not isinstance(frame.get("access_token"), str):
            await websocket.close(code=4401)
            return
        try:
            async with session_factory() as db:
                await authenticate_channel(db, channel_id, frame["access_token"])
        except AppError as exc:
            code = 4403 if exc.status_code == 403 else 4404 if exc.status_code == 404 else 4401
            await websocket.close(code=code)
            return
        await channel_connections.connect(channel_id, websocket)
        registered = True
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        if registered:
            channel_connections.disconnect(channel_id, websocket)
