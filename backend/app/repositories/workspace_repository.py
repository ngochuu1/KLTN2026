from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember


class WorkspaceRepository:
    """Query/flush only. Caller creates the OWNER in the same creation transaction."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, name: str, description: str | None = None) -> Workspace:
        workspace = Workspace(name=name, description=description)
        self.session.add(workspace)
        await self.session.flush()
        await self.session.refresh(workspace)
        return workspace

    async def get_by_id(self, workspace_id: UUID, *, active_only: bool = True, for_update: bool = False) -> Workspace | None:
        statement = select(Workspace).where(Workspace.id == workspace_id)
        if active_only:
            statement = statement.where(Workspace.deleted_at.is_(None))
        if for_update:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        return await self.session.scalar(statement)

    async def list_active(self) -> list[Workspace]:
        return list(await self.session.scalars(select(Workspace).where(Workspace.deleted_at.is_(None)).order_by(Workspace.created_at, Workspace.id)))

    async def update(self, workspace: Workspace, *, name: str, description: str | None) -> Workspace:
        workspace.name = name
        workspace.description = description
        await self.session.flush()
        await self.session.refresh(workspace)
        return workspace

    async def soft_delete(self, workspace: Workspace, *, now: datetime) -> None:
        if workspace.deleted_at is None:
            workspace.deleted_at = now
            await self.session.flush()
            await self.session.refresh(workspace)

    async def list_for_user(self, user_id: UUID) -> list[tuple[Workspace, WorkspaceMember]]:
        rows = await self.session.execute(
            select(Workspace, WorkspaceMember).join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(WorkspaceMember.user_id == user_id, Workspace.deleted_at.is_(None))
            .order_by(Workspace.created_at, Workspace.id)
        )
        return list(rows.tuples())
