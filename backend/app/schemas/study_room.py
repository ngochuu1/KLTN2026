from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.channel import ChannelResponse


class RoomParticipant(BaseModel):
    user_id: UUID
    full_name: str
    state: Literal["IN_ROOM"]
    joined_at: datetime
    microphone_enabled: bool
    camera_enabled: bool
    screen_sharing: bool


class RoomDetails(BaseModel):
    channel: ChannelResponse
    participants: list[RoomParticipant]


class MediaCredential(BaseModel):
    url: str
    token: str
    room: str
    identity: str
