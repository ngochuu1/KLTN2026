"""default_channel_backfill

Revision ID: 20260926_02
Revises: 20260926_01
Create Date: 2026-09-26
"""
from typing import Sequence, Union

from alembic import op


revision: str = "20260926_02"
down_revision: Union[str, Sequence[str], None] = "20260926_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Promote an existing general channel only when the workspace has no default.
    op.execute("""
        UPDATE channels AS candidate
        SET is_default = true, updated_at = now()
        WHERE candidate.name = 'general'
          AND candidate.is_default = false
          AND NOT EXISTS (
              SELECT 1 FROM channels AS current_default
              WHERE current_default.workspace_id = candidate.workspace_id
                AND current_default.is_default = true
          )
    """)
    # The deterministic UUID and conflict guard make the desired data result idempotent.
    op.execute("""
        INSERT INTO channels (id, workspace_id, name, description, type, is_default)
        SELECT md5(workspace.id::text || '-default-general')::uuid,
               workspace.id, 'general', NULL, 'TEXT', true
        FROM workspaces AS workspace
        WHERE NOT EXISTS (
                  SELECT 1 FROM channels AS current_default
                  WHERE current_default.workspace_id = workspace.id
                    AND current_default.is_default = true
              )
          AND NOT EXISTS (
                  SELECT 1 FROM channels AS general
                  WHERE general.workspace_id = workspace.id
                    AND general.name = 'general'
              )
        ON CONFLICT DO NOTHING
    """)


def downgrade() -> None:
    # Backfilled channels remain valid Phase 3A data; destructive data reversal is unsafe.
    pass
