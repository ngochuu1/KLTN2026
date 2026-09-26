from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String, Text, UniqueConstraint, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ChannelType


class Channel(Base):
    __tablename__ = "channels"
    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="uq_channels_workspace_name"),
        Index("uq_channels_workspace_default", "workspace_id", unique=True, postgresql_where=text("is_default")),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[ChannelType] = mapped_column(
        Enum(ChannelType, native_enum=False, create_constraint=True, name="ck_channels_type"), nullable=False,
    )
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    workspace: Mapped["Workspace"] = relationship(back_populates="channels", lazy="raise")
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="channel", lazy="raise", passive_deletes=True)
