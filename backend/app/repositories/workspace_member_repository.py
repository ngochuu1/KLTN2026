from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import WorkspaceRole
from app.models.workspace_member import WorkspaceMember


class WorkspaceMemberRepository:
    """Caller owns transactions and authorization; system_role grants no workspace rights.

    Creation flow must explicitly insert the creator as OWNER. Ordinary joins
    default to MEMBER. UC12 may only switch ADMIN/MEMBER, by an OWNER actor.
    OWNER removal/role mutation is excluded atomically by the write predicates.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, workspace_id: UUID, user_id: UUID, role: WorkspaceRole = WorkspaceRole.MEMBER) -> WorkspaceMember:
        member = WorkspaceMember(workspace_id=workspace_id, user_id=user_id, role=role)
        self.session.add(member)
        await self.session.flush()
        await self.session.refresh(member)
        return member

    async def get_membership(self, workspace_id: UUID, user_id: UUID, *, for_update: bool = False) -> WorkspaceMember | None:
        statement = select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id)
        if for_update:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        return await self.session.scalar(statement)

    async def list_members(self, workspace_id: UUID) -> list[WorkspaceMember]:
        return list(await self.session.scalars(select(WorkspaceMember).options(selectinload(WorkspaceMember.user)).where(WorkspaceMember.workspace_id == workspace_id).order_by(WorkspaceMember.joined_at, WorkspaceMember.id)))

    async def check_membership(self, workspace_id: UUID, user_id: UUID) -> bool:
        return await self.get_membership(workspace_id, user_id) is not None

    async def update_role(self, workspace_id: UUID, user_id: UUID, *, role: WorkspaceRole) -> WorkspaceMember | None:
        if role not in (WorkspaceRole.ADMIN, WorkspaceRole.MEMBER):
            raise ValueError("Only ADMIN and MEMBER are assignable roles")
        return await self.session.scalar(
            update(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.role != WorkspaceRole.OWNER,
            ).values(role=role).returning(WorkspaceMember).execution_options(populate_existing=True)
        )

    async def remove(self, workspace_id: UUID, user_id: UUID) -> bool:
        removed = await self.session.scalar(delete(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.role != WorkspaceRole.OWNER,
        ).returning(WorkspaceMember.id))
        return removed is not None
