from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (Index("ix_chat_messages_channel_created_at", "channel_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    channel_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("channels.id", ondelete="CASCADE"), nullable=False)
    sender_user_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False, index=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    channel: Mapped["Channel"] = relationship(back_populates="messages", lazy="raise")
    sender: Mapped["User"] = relationship(lazy="raise")
    attachments: Mapped[list["ChatAttachment"]] = relationship(back_populates="message", lazy="raise", passive_deletes=True)
    reactions: Mapped[list["MessageReaction"]] = relationship(back_populates="message", lazy="raise", passive_deletes=True)
