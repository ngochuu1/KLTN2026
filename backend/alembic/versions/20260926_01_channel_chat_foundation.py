"""channel_chat_foundation

Revision ID: 20260926_01
Revises: 20260925_01
Create Date: 2026-09-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260926_01"
down_revision: Union[str, Sequence[str], None] = "20260925_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "channels",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("type", sa.Enum("TEXT", "STUDY_ROOM", name="ck_channels_type", native_enum=False, create_constraint=True), nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "name", name="uq_channels_workspace_name"),
    )
    op.create_index(op.f("ix_channels_workspace_id"), "channels", ["workspace_id"], unique=False)
    op.create_index("uq_channels_workspace_default", "channels", ["workspace_id"], unique=True, postgresql_where=sa.text("is_default"))

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("channel_id", sa.Uuid(), nullable=False),
        sa.Column("sender_user_id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_messages_channel_created_at", "chat_messages", ["channel_id", "created_at"], unique=False)
    op.create_index(op.f("ix_chat_messages_sender_user_id"), "chat_messages", ["sender_user_id"], unique=False)

    op.create_table(
        "chat_attachments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("message_id", sa.Uuid(), nullable=False),
        sa.Column("storage_key", sa.String(), nullable=False),
        sa.Column("original_filename", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["chat_messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chat_attachments_message_id"), "chat_attachments", ["message_id"], unique=False)

    op.create_table(
        "message_reactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("message_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("emoji", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["chat_messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id", "user_id", "emoji", name="uq_message_reactions_message_user_emoji"),
    )
    op.create_index(op.f("ix_message_reactions_message_id"), "message_reactions", ["message_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_message_reactions_message_id"), table_name="message_reactions")
    op.drop_table("message_reactions")
    op.drop_index(op.f("ix_chat_attachments_message_id"), table_name="chat_attachments")
    op.drop_table("chat_attachments")
    op.drop_index(op.f("ix_chat_messages_sender_user_id"), table_name="chat_messages")
    op.drop_index("ix_chat_messages_channel_created_at", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_index("uq_channels_workspace_default", table_name="channels", postgresql_where=sa.text("is_default"))
    op.drop_index(op.f("ix_channels_workspace_id"), table_name="channels")
    op.drop_table("channels")
