from uuid import UUID

from fastapi import APIRouter, Response

from app.api.dependencies import CurrentPrincipal, DbSession
from app.schemas.channel import ChannelCreateRequest, ChannelResponse, ChannelUpdateRequest
from app.schemas.common import DataResponse, ErrorResponse
from app.services.channel_service import ChannelService

router = APIRouter(tags=["channels"], responses={
    status: {"model": ErrorResponse} for status in (401, 403, 404, 409, 422)
})


@router.post("/workspaces/{workspace_id}/channels", status_code=201, response_model=DataResponse[ChannelResponse])
async def create(workspace_id: UUID, request: ChannelCreateRequest, principal: CurrentPrincipal, db: DbSession):
    return DataResponse(data=await ChannelService(db).create(principal, workspace_id, request))


@router.get("/workspaces/{workspace_id}/channels", response_model=DataResponse[list[ChannelResponse]])
async def list_channels(workspace_id: UUID, principal: CurrentPrincipal, db: DbSession):
    return DataResponse(data=await ChannelService(db).list(principal, workspace_id))


@router.get("/channels/{channel_id}", response_model=DataResponse[ChannelResponse])
async def detail(channel_id: UUID, principal: CurrentPrincipal, db: DbSession):
    return DataResponse(data=await ChannelService(db).detail(principal, channel_id))


@router.patch("/channels/{channel_id}", response_model=DataResponse[ChannelResponse])
async def update(channel_id: UUID, request: ChannelUpdateRequest, principal: CurrentPrincipal, db: DbSession):
    return DataResponse(data=await ChannelService(db).update(principal, channel_id, request))


@router.delete("/channels/{channel_id}", status_code=204, response_class=Response)
async def delete(channel_id: UUID, principal: CurrentPrincipal, db: DbSession):
    await ChannelService(db).delete(principal, channel_id)
    return Response(status_code=204)
