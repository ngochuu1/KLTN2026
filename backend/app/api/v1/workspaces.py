from uuid import UUID

from fastapi import APIRouter, Response

from app.api.dependencies import CurrentPrincipal, DbSession
from app.schemas.common import DataResponse, ErrorResponse
from app.schemas.workspace import (
    InvitationCreateRequest, InvitationCreatedResponse, MemberResponse, MemberRoleRequest,
    WorkspaceCreateRequest, WorkspaceResponse, WorkspaceUpdateRequest,
)
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"],
                   responses={s: {"model": ErrorResponse} for s in (401, 403, 404, 409, 422)})


@router.post("", status_code=201, response_model=DataResponse[WorkspaceResponse])
async def create(request: WorkspaceCreateRequest, principal: CurrentPrincipal, db: DbSession):
    return DataResponse(data=await WorkspaceService(db).create(principal, request))


@router.get("", response_model=DataResponse[list[WorkspaceResponse]])
async def list_workspaces(principal: CurrentPrincipal, db: DbSession):
    return DataResponse(data=await WorkspaceService(db).list_workspaces(principal))


@router.get("/{workspace_id}", response_model=DataResponse[WorkspaceResponse])
async def detail(workspace_id: UUID, principal: CurrentPrincipal, db: DbSession):
    return DataResponse(data=await WorkspaceService(db).detail(principal, workspace_id))


@router.patch("/{workspace_id}", response_model=DataResponse[WorkspaceResponse])
async def update(workspace_id: UUID, request: WorkspaceUpdateRequest, principal: CurrentPrincipal, db: DbSession):
    return DataResponse(data=await WorkspaceService(db).update(principal, workspace_id, request))


@router.delete("/{workspace_id}", status_code=204, response_class=Response)
async def delete(workspace_id: UUID, principal: CurrentPrincipal, db: DbSession):
    await WorkspaceService(db).delete(principal, workspace_id)
    return Response(status_code=204)


@router.post("/{workspace_id}/invitations", status_code=201, response_model=DataResponse[InvitationCreatedResponse])
async def create_invitation(workspace_id: UUID, request: InvitationCreateRequest, principal: CurrentPrincipal, db: DbSession, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return DataResponse(data=await WorkspaceService(db).create_invitation(principal, workspace_id, request))


@router.get("/{workspace_id}/members", response_model=DataResponse[list[MemberResponse]])
async def list_members(workspace_id: UUID, principal: CurrentPrincipal, db: DbSession):
    return DataResponse(data=await WorkspaceService(db).list_members(principal, workspace_id))


@router.delete("/{workspace_id}/members/{user_id}", status_code=204, response_class=Response)
async def remove_member(workspace_id: UUID, user_id: UUID, principal: CurrentPrincipal, db: DbSession):
    await WorkspaceService(db).remove_member(principal, workspace_id, user_id)
    return Response(status_code=204)


@router.patch("/{workspace_id}/members/{user_id}/role", response_model=DataResponse[MemberResponse])
async def change_role(workspace_id: UUID, user_id: UUID, request: MemberRoleRequest, principal: CurrentPrincipal, db: DbSession):
    return DataResponse(data=await WorkspaceService(db).change_role(principal, workspace_id, user_id, request.role))


@router.post("/{workspace_id}/leave", status_code=204, response_class=Response)
async def leave(workspace_id: UUID, principal: CurrentPrincipal, db: DbSession):
    await WorkspaceService(db).leave(principal, workspace_id)
    return Response(status_code=204)
