from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.models.enums import ChannelType, WorkspaceRole
from app.repositories.channel_repository import ChannelRepository
from app.repositories.workspace_member_repository import WorkspaceMemberRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.channel import ChannelCreateRequest, ChannelResponse, ChannelUpdateRequest
from app.services.auth_service import AuthService, Principal


class ChannelService:
    MANAGERS = {WorkspaceRole.OWNER, WorkspaceRole.ADMIN}

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.channels = ChannelRepository(db)
        self.workspaces = WorkspaceRepository(db)
        self.members = WorkspaceMemberRepository(db)

    @asynccontextmanager
    async def transaction(self, principal: Principal):
        try:
            async with self.db.begin():
                await AuthService(self.db).load_principal(principal.user.id, principal.session.id)
                yield
        except IntegrityError as exc:
            cause = exc.orig.__cause__
            if getattr(cause, "constraint_name", None) == "uq_channels_workspace_name":
                raise AppError(409, "CHANNEL_NAME_ALREADY_EXISTS", "Tên Channel đã tồn tại") from None
            raise

    async def workspace_access(self, workspace_id: UUID, user_id: UUID, allowed=None):
        workspace = await self.workspaces.get_by_id(workspace_id, for_update=True)
        if workspace is None:
            raise AppError(404, "WORKSPACE_NOT_FOUND", "Không tìm thấy Workspace")
        member = await self.members.get_membership(workspace_id, user_id)
        if member is None or (allowed is not None and member.role not in allowed):
            raise AppError(403, "CHANNEL_PERMISSION_DENIED", "Bạn không có quyền truy cập Channel")
        return workspace, member

    async def channel_access(self, channel_id: UUID, user_id: UUID, allowed=None):
        channel = await self.channels.get_by_id(channel_id, for_update=True)
        if channel is None:
            raise AppError(404, "CHANNEL_NOT_FOUND", "Không tìm thấy Channel")
        workspace = await self.workspaces.get_by_id(channel.workspace_id, for_update=True)
        if workspace is None:
            raise AppError(404, "CHANNEL_NOT_FOUND", "Không tìm thấy Channel")
        member = await self.members.get_membership(workspace.id, user_id)
        if member is None or (allowed is not None and member.role not in allowed):
            raise AppError(403, "CHANNEL_PERMISSION_DENIED", "Bạn không có quyền truy cập Channel")
        return channel

    @staticmethod
    def response(channel) -> ChannelResponse:
        return ChannelResponse.model_validate(channel)

    async def create(self, principal: Principal, workspace_id: UUID, request: ChannelCreateRequest):
        async with self.transaction(principal):
            await self.workspace_access(workspace_id, principal.user.id, self.MANAGERS)
            try:
                channel_type = ChannelType(request.type)
            except ValueError:
                raise AppError(422, "INVALID_CHANNEL_TYPE", "Loại Channel không hợp lệ") from None
            if await self.channels.name_exists(workspace_id, request.name):
                raise AppError(409, "CHANNEL_NAME_ALREADY_EXISTS", "Tên Channel đã tồn tại")
            channel = await self.channels.create(
                workspace_id=workspace_id, name=request.name, description=request.description, type=channel_type,
            )
            result = self.response(channel)
        return result

    async def list(self, principal: Principal, workspace_id: UUID):
        async with self.transaction(principal):
            await self.workspace_access(workspace_id, principal.user.id)
            result = [self.response(channel) for channel in await self.channels.list_by_workspace(workspace_id)]
        return result

    async def detail(self, principal: Principal, channel_id: UUID):
        async with self.transaction(principal):
            channel = await self.channel_access(channel_id, principal.user.id)
            result = self.response(channel)
        return result

    async def update(self, principal: Principal, channel_id: UUID, request: ChannelUpdateRequest):
        async with self.transaction(principal):
            channel = await self.channel_access(channel_id, principal.user.id, self.MANAGERS)
            changes = request.model_dump(exclude_unset=True)
            name = changes.get("name", channel.name)
            if await self.channels.name_exists(channel.workspace_id, name, exclude_channel_id=channel.id):
                raise AppError(409, "CHANNEL_NAME_ALREADY_EXISTS", "Tên Channel đã tồn tại")
            await self.channels.update(
                channel, name=name, description=changes.get("description", channel.description),
            )
            result = self.response(channel)
        return result

    async def delete(self, principal: Principal, channel_id: UUID):
        async with self.transaction(principal):
            channel = await self.channel_access(channel_id, principal.user.id, self.MANAGERS)
            if channel.is_default:
                raise AppError(403, "DEFAULT_CHANNEL_CANNOT_BE_DELETED", "Không thể xóa Channel mặc định")
            await self.channels.delete(channel)
