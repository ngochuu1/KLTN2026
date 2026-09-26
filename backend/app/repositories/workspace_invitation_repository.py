from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import InvitationStatus
from app.models.workspace_invitation import WorkspaceInvitation


class WorkspaceInvitationRepository:
    """Caller supplies a cryptographic token hash, never a raw token/code.

    Caller owns transactions, authorization, expiry and status transition rules.
    No invitation lifetime is chosen here.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, workspace_id: UUID, created_by_user_id: UUID, token_hash: str,
                     invitee_user_id: UUID | None = None, expires_at: datetime | None = None) -> WorkspaceInvitation:
        invitation = WorkspaceInvitation(workspace_id=workspace_id, created_by_user_id=created_by_user_id,
                                         invitee_user_id=invitee_user_id, token_hash=token_hash, expires_at=expires_at)
        self.session.add(invitation)
        await self.session.flush()
        await self.session.refresh(invitation)
        return invitation

    async def get_by_id(self, invitation_id: UUID, *, for_update: bool = False) -> WorkspaceInvitation | None:
        statement = select(WorkspaceInvitation).where(WorkspaceInvitation.id == invitation_id)
        if for_update:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        return await self.session.scalar(statement)

    async def get_by_token_hash(self, token_hash: str, *, for_update: bool = False) -> WorkspaceInvitation | None:
        statement = select(WorkspaceInvitation).where(WorkspaceInvitation.token_hash == token_hash)
        if for_update:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        return await self.session.scalar(statement)

    async def update_status(self, invitation: WorkspaceInvitation, *, status: InvitationStatus) -> WorkspaceInvitation:
        invitation.status = status
        await self.session.flush()
        await self.session.refresh(invitation)
        return invitation
