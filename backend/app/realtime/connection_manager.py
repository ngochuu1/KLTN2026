from collections import defaultdict
from uuid import UUID

from fastapi import WebSocket


class ChannelConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[UUID, set[WebSocket]] = defaultdict(set)

    async def connect(self, channel_id: UUID, websocket: WebSocket) -> None:
        self._connections[channel_id].add(websocket)

    def disconnect(self, channel_id: UUID, websocket: WebSocket) -> None:
        connections = self._connections.get(channel_id)
        if connections is None:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(channel_id, None)

    async def broadcast(self, channel_id: UUID, event: dict) -> None:
        dead: list[WebSocket] = []
        for websocket in tuple(self._connections.get(channel_id, ())):
            try:
                await websocket.send_json(event)
            except Exception:
                dead.append(websocket)
        for websocket in dead:
            self.disconnect(channel_id, websocket)

    def connection_count(self, channel_id: UUID) -> int:
        return len(self._connections.get(channel_id, ()))


channel_connections = ChannelConnectionManager()
