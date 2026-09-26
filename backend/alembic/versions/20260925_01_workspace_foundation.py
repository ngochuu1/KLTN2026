"""workspace_foundation

Revision ID: 20260925_01
Revises: 20260924_01
Create Date: 2026-09-25 23:56:23.310191
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260925_01'
down_revision: Union[str, Sequence[str], None] = '20260924_01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('workspaces',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('workspace_invitations',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('workspace_id', sa.Uuid(), nullable=False),
    sa.Column('created_by_user_id', sa.Uuid(), nullable=False),
    sa.Column('invitee_user_id', sa.Uuid(), nullable=True),
    sa.Column('token_hash', sa.String(length=255), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'ACCEPTED', 'DECLINED', 'REVOKED', name='ck_workspace_invitations_status', native_enum=False, create_constraint=True), server_default='PENDING', nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['invitee_user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('token_hash')
    )
    op.create_index(op.f('ix_workspace_invitations_workspace_id'), 'workspace_invitations', ['workspace_id'], unique=False)
    op.create_table('workspace_members',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('workspace_id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('role', sa.Enum('OWNER', 'ADMIN', 'MEMBER', name='ck_workspace_members_role', native_enum=False, create_constraint=True), server_default='MEMBER', nullable=False),
    sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('workspace_id', 'user_id', name='uq_workspace_members_workspace_user')
    )
    op.create_index(op.f('ix_workspace_members_user_id'), 'workspace_members', ['user_id'], unique=False)
    op.create_index('uq_workspace_members_owner', 'workspace_members', ['workspace_id'], unique=True, postgresql_where=sa.text("role = 'OWNER'"))


def downgrade() -> None:
    op.drop_index('uq_workspace_members_owner', table_name='workspace_members', postgresql_where=sa.text("role = 'OWNER'"))
    op.drop_index(op.f('ix_workspace_members_user_id'), table_name='workspace_members')
    op.drop_table('workspace_members')
    op.drop_index(op.f('ix_workspace_invitations_workspace_id'), table_name='workspace_invitations')
    op.drop_table('workspace_invitations')
    op.drop_table('workspaces')
