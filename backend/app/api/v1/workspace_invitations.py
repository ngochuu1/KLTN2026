from fastapi import APIRouter

from app.api.dependencies import CurrentPrincipal, DbSession
from app.schemas.common import DataResponse, ErrorResponse
from app.schemas.workspace import InvitationPreviewResponse, InvitationResponse, WorkspaceResponse
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/workspace-invitations", tags=["workspace-invitations"],
                   responses={s: {"model": ErrorResponse} for s in (401, 403, 404, 409, 410, 422)})


@router.get("/{token}", response_model=DataResponse[InvitationPreviewResponse])
async def preview(token: str, principal: CurrentPrincipal, db: DbSession):
    return DataResponse(data=await WorkspaceService(db).preview(principal, token))


@router.post("/{token}/accept", response_model=DataResponse[WorkspaceResponse])
async def accept(token: str, principal: CurrentPrincipal, db: DbSession):
    return DataResponse(data=await WorkspaceService(db).accept(principal, token))


@router.post("/{token}/decline", response_model=DataResponse[InvitationResponse])
async def decline(token: str, principal: CurrentPrincipal, db: DbSession):
    return DataResponse(data=await WorkspaceService(db).decline(principal, token))
