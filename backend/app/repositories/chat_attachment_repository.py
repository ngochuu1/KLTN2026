from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat_attachment import ChatAttachment


class ChatAttachmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, message_id: UUID, storage_key: str, original_filename: str, content_type: str, size_bytes: int) -> ChatAttachment:
        attachment = ChatAttachment(
            message_id=message_id, storage_key=storage_key, original_filename=original_filename,
            content_type=content_type, size_bytes=size_bytes,
        )
        self.session.add(attachment)
        await self.session.flush()
        await self.session.refresh(attachment)
        return attachment

    async def list_by_message(self, message_id: UUID) -> list[ChatAttachment]:
        return list(await self.session.scalars(
            select(ChatAttachment).where(ChatAttachment.message_id == message_id).order_by(ChatAttachment.created_at, ChatAttachment.id)
        ))

    async def get_with_message(self, attachment_id: UUID) -> ChatAttachment | None:
        return await self.session.scalar(
            select(ChatAttachment)
            .options(selectinload(ChatAttachment.message))
            .where(ChatAttachment.id == attachment_id)
        )
