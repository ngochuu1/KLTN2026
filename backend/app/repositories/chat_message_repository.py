from datetime import datetime
from uuid import UUID

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat_message import ChatMessage
from app.models.message_reaction import MessageReaction


class ChatMessageRepository:
    """Persistence operations only; message validity and permissions belong to services."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, channel_id: UUID, sender_user_id: UUID, content: str | None = None) -> ChatMessage:
        message = ChatMessage(channel_id=channel_id, sender_user_id=sender_user_id, content=content)
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def get_by_id(self, message_id: UUID, *, for_update: bool = False) -> ChatMessage | None:
        statement = select(ChatMessage).where(ChatMessage.id == message_id)
        if for_update:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        return await self.session.scalar(statement)

    async def list_by_channel(self, channel_id: UUID) -> list[ChatMessage]:
        return list(await self.session.scalars(
            select(ChatMessage).where(ChatMessage.channel_id == channel_id).order_by(ChatMessage.created_at, ChatMessage.id)
        ))

    async def list_history(self, channel_id: UUID, *, limit: int, before: ChatMessage | None = None) -> list[ChatMessage]:
        statement = (
            select(ChatMessage)
            .options(
                selectinload(ChatMessage.sender), selectinload(ChatMessage.reactions),
                selectinload(ChatMessage.attachments),
            )
            .where(ChatMessage.channel_id == channel_id, ChatMessage.deleted_at.is_(None))
        )
        if before is not None:
            statement = statement.where(tuple_(ChatMessage.created_at, ChatMessage.id) < (before.created_at, before.id))
        return list(await self.session.scalars(
            statement.order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc()).limit(limit)
        ))

    async def get_with_details(self, message_id: UUID) -> ChatMessage | None:
        return await self.session.scalar(
            select(ChatMessage)
            .options(
                selectinload(ChatMessage.sender), selectinload(ChatMessage.reactions),
                selectinload(ChatMessage.attachments),
            )
            .where(ChatMessage.id == message_id)
            .execution_options(populate_existing=True)
        )

    async def update_content(self, message: ChatMessage, *, content: str | None, edited_at: datetime) -> ChatMessage:
        message.content = content
        message.edited_at = edited_at
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def mark_deleted(self, message: ChatMessage, *, deleted_at: datetime) -> ChatMessage:
        message.deleted_at = deleted_at
        await self.session.flush()
        await self.session.refresh(message)
        return message
