from contextlib import asynccontextmanager
from datetime import UTC, datetime
import hashlib
import secrets
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.models.enums import ChannelType, InvitationStatus, WorkspaceRole
from app.repositories.channel_repository import ChannelRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.repositories.workspace_member_repository import WorkspaceMemberRepository
from app.repositories.workspace_invitation_repository import WorkspaceInvitationRepository
from app.schemas.workspace import (
    InvitationCreatedResponse, InvitationCreateRequest, InvitationPreviewResponse,
    InvitationResponse, MemberResponse, WorkspaceCreateRequest, WorkspaceResponse,
    WorkspaceUpdateRequest,
)
from app.services.auth_service import AuthService, Principal


class WorkspaceService:
    # Every workspace operation locks Workspace before reading membership/permissions.
    # Mutations therefore serialize with delete, role changes, removal and acceptance.
    MANAGERS = {WorkspaceRole.OWNER, WorkspaceRole.ADMIN}

    def __init__(self, db: AsyncSession):
        self.db = db
        self.workspaces = WorkspaceRepository(db)
        self.members = WorkspaceMemberRepository(db)
        self.invitations = WorkspaceInvitationRepository(db)
        self.users = UserRepository(db)
        self.channels = ChannelRepository(db)

    @asynccontextmanager
    async def transaction(self, principal: Principal):
        try:
            async with self.db.begin():
                await AuthService(self.db).load_principal(principal.user.id, principal.session.id)
                yield
        except IntegrityError as exc:
            cause = exc.orig.__cause__
            if getattr(cause, "constraint_name", None) == "uq_workspace_members_workspace_user":
                raise AppError(409, "WORKSPACE_ALREADY_MEMBER", "Người dùng đã là thành viên") from None
            raise

    async def active_workspace(self, workspace_id: UUID):
        workspace = await self.workspaces.get_by_id(workspace_id, for_update=True)
        if workspace is None:
            raise AppError(404, "WORKSPACE_NOT_FOUND", "Không tìm thấy Workspace")
        return workspace

    async def access(self, workspace_id: UUID, user_id: UUID, allowed=None):
        workspace = await self.active_workspace(workspace_id)
        member = await self.members.get_membership(workspace_id, user_id)
        if member is None:
            raise AppError(403, "WORKSPACE_ACCESS_DENIED", "Bạn không thuộc Workspace")
        if allowed is not None and member.role not in allowed:
            raise AppError(403, "WORKSPACE_PERMISSION_DENIED", "Bạn không có quyền thực hiện thao tác")
        return workspace, member

    @staticmethod
    def workspace_response(workspace, role):
        return WorkspaceResponse(id=workspace.id, name=workspace.name, description=workspace.description,
                                 created_at=workspace.created_at, updated_at=workspace.updated_at, role=role)

    @staticmethod
    def member_response(member):
        return MemberResponse(user_id=member.user_id, full_name=member.user.full_name,
                              email=member.user.email, role=member.role, joined_at=member.joined_at)

    async def create(self, principal: Principal, request: WorkspaceCreateRequest):
        async with self.transaction(principal):
            workspace = await self.workspaces.create(name=request.name, description=request.description)
            member = await self.members.create(workspace_id=workspace.id, user_id=principal.user.id, role=WorkspaceRole.OWNER)
            await self.channels.create(
                workspace_id=workspace.id, name="general", type=ChannelType.TEXT, is_default=True,
            )
            result = self.workspace_response(workspace, member.role)
        return result

    async def list_workspaces(self, principal: Principal):
        async with self.transaction(principal):
            return [self.workspace_response(w, m.role) for w, m in await self.workspaces.list_for_user(principal.user.id)]

    async def detail(self, principal: Principal, workspace_id: UUID):
        async with self.transaction(principal):
            workspace, member = await self.access(workspace_id, principal.user.id)
            return self.workspace_response(workspace, member.role)

    async def update(self, principal: Principal, workspace_id: UUID, request: WorkspaceUpdateRequest):
        async with self.transaction(principal):
            workspace, member = await self.access(workspace_id, principal.user.id, self.MANAGERS)
            changes = request.model_dump(exclude_unset=True)
            await self.workspaces.update(workspace, name=changes.get("name", workspace.name),
                                         description=changes.get("description", workspace.description))
            result = self.workspace_response(workspace, member.role)
        return result

    async def delete(self, principal: Principal, workspace_id: UUID):
        async with self.transaction(principal):
            workspace, _ = await self.access(workspace_id, principal.user.id, {WorkspaceRole.OWNER})
            await self.workspaces.soft_delete(workspace, now=datetime.now(UTC))

    async def create_invitation(self, principal: Principal, workspace_id: UUID, request: InvitationCreateRequest):
        async with self.transaction(principal):
            await self.access(workspace_id, principal.user.id, self.MANAGERS)
            if request.invitee_user_id is not None:
                if await self.users.get_by_id(request.invitee_user_id) is None:
                    raise AppError(404, "USER_NOT_FOUND", "Không tìm thấy người dùng được mời")
                if await self.members.check_membership(workspace_id, request.invitee_user_id):
                    raise AppError(409, "WORKSPACE_ALREADY_MEMBER", "Người dùng đã là thành viên")
            token = secrets.token_urlsafe(32)
            invitation = await self.invitations.create(
                workspace_id=workspace_id, created_by_user_id=principal.user.id,
                invitee_user_id=request.invitee_user_id, expires_at=request.expires_at,
                token_hash=hashlib.sha256(token.encode()).hexdigest(),
            )
            result = InvitationCreatedResponse(**InvitationResponse.model_validate(invitation).model_dump(), token=token)
        return result

    async def valid_invitation(self, token: str, user_id: UUID):
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        candidate = await self.invitations.get_by_token_hash(token_hash)
        if candidate is None:
            raise AppError(404, "INVITATION_INVALID", "Lời mời không hợp lệ")
        # Lock order is Workspace -> Invitation for all invitation operations.
        workspace = await self.active_workspace(candidate.workspace_id)
        invitation = await self.invitations.get_by_token_hash(token_hash, for_update=True)
        if invitation is None:
            raise AppError(404, "INVITATION_INVALID", "Lời mời không hợp lệ")
        if invitation.status != InvitationStatus.PENDING:
            raise AppError(409, "INVITATION_ALREADY_USED", "Lời mời không còn khả dụng")
        if invitation.is_expired(datetime.now(UTC)):
            raise AppError(410, "INVITATION_EXPIRED", "Lời mời đã hết hạn")
        if invitation.invitee_user_id is not None and invitation.invitee_user_id != user_id:
            raise AppError(403, "INVITATION_NOT_FOR_USER", "Lời mời không dành cho bạn")
        if await self.members.check_membership(workspace.id, user_id):
            raise AppError(409, "WORKSPACE_ALREADY_MEMBER", "Bạn đã là thành viên")
        return workspace, invitation

    async def preview(self, principal: Principal, token: str):
        async with self.transaction(principal):
            workspace, invitation = await self.valid_invitation(token, principal.user.id)
            return InvitationPreviewResponse(workspace_id=workspace.id, name=workspace.name,
                                             description=workspace.description, expires_at=invitation.expires_at)

    async def accept(self, principal: Principal, token: str):
        async with self.transaction(principal):
            workspace, invitation = await self.valid_invitation(token, principal.user.id)
            member = await self.members.create(workspace_id=workspace.id, user_id=principal.user.id, role=WorkspaceRole.MEMBER)
            await self.invitations.update_status(invitation, status=InvitationStatus.ACCEPTED)
            result = self.workspace_response(workspace, member.role)
        return result

    async def decline(self, principal: Principal, token: str):
        async with self.transaction(principal):
            _, invitation = await self.valid_invitation(token, principal.user.id)
            await self.invitations.update_status(invitation, status=InvitationStatus.DECLINED)
            result = InvitationResponse.model_validate(invitation)
        return result

    async def list_members(self, principal: Principal, workspace_id: UUID):
        async with self.transaction(principal):
            await self.access(workspace_id, principal.user.id)
            return [self.member_response(m) for m in await self.members.list_members(workspace_id)]

    async def target_member(self, workspace_id: UUID, user_id: UUID):
        target = await self.members.get_membership(workspace_id, user_id)
        if target is None:
            raise AppError(404, "WORKSPACE_MEMBER_NOT_FOUND", "Không tìm thấy thành viên")
        return target

    async def remove_member(self, principal: Principal, workspace_id: UUID, user_id: UUID):
        async with self.transaction(principal):
            await self.access(workspace_id, principal.user.id, self.MANAGERS)
            target = await self.target_member(workspace_id, user_id)
            if target.role == WorkspaceRole.OWNER:
                raise AppError(403, "WORKSPACE_OWNER_CANNOT_BE_REMOVED", "Không thể xóa OWNER")
            await self.members.remove(workspace_id, user_id)

    async def change_role(self, principal: Principal, workspace_id: UUID, user_id: UUID, role: str):
        async with self.transaction(principal):
            await self.access(workspace_id, principal.user.id, {WorkspaceRole.OWNER})
            if role not in (WorkspaceRole.ADMIN, WorkspaceRole.MEMBER):
                raise AppError(422, "INVALID_WORKSPACE_ROLE", "Chỉ được gán ADMIN hoặc MEMBER")
            target = await self.target_member(workspace_id, user_id)
            if target.role == WorkspaceRole.OWNER:
                raise AppError(403, "INVALID_WORKSPACE_ROLE", "Không thể thay đổi role OWNER")
            await self.members.update_role(workspace_id, user_id, role=WorkspaceRole(role))
            members = await self.members.list_members(workspace_id)
            result = self.member_response(next(m for m in members if m.user_id == user_id))
        return result

    async def leave(self, principal: Principal, workspace_id: UUID):
        async with self.transaction(principal):
            _, member = await self.access(workspace_id, principal.user.id)
            if member.role == WorkspaceRole.OWNER:
                raise AppError(403, "WORKSPACE_OWNER_CANNOT_LEAVE", "OWNER không được rời Workspace")
            await self.members.remove(workspace_id, principal.user.id)
