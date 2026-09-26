from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MessageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    content: str | None


class MessageSenderResponse(BaseModel):
    id: UUID
    full_name: str


class ReactionSummaryResponse(BaseModel):
    emoji: str
    count: int


class AttachmentResponse(BaseModel):
    id: UUID
    original_filename: str
    content_type: str
    size_bytes: int


class MessageResponse(BaseModel):
    id: UUID
    channel_id: UUID
    content: str | None
    sender: MessageSenderResponse
    created_at: datetime
    edited_at: datetime | None
    reactions: list[ReactionSummaryResponse]
    attachments: list[AttachmentResponse]
