from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, Path, Query, Response, UploadFile
from fastapi.responses import RedirectResponse

from app.api.dependencies import CurrentPrincipal, DbSession
from app.schemas.chat import MessageRequest, MessageResponse, ReactionSummaryResponse
from app.schemas.common import DataResponse, ErrorResponse
from app.services.chat_service import ChatService

router = APIRouter(tags=["chat"], responses={
    status: {"model": ErrorResponse} for status in (401, 403, 404, 409, 413, 422, 503)
})


@router.get("/channels/{channel_id}/messages", response_model=DataResponse[list[MessageResponse]])
async def history(
    channel_id: UUID, principal: CurrentPrincipal, db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    before_message_id: UUID | None = None,
):
    return DataResponse(data=await ChatService(db).history(
        principal, channel_id, limit=limit, before_message_id=before_message_id,
    ))


@router.post("/channels/{channel_id}/messages", status_code=201, response_model=DataResponse[MessageResponse])
async def send(channel_id: UUID, request: MessageRequest, principal: CurrentPrincipal, db: DbSession):
    return DataResponse(data=await ChatService(db).send(principal, channel_id, request))


@router.post(
    "/channels/{channel_id}/messages/attachments", status_code=201,
    response_model=DataResponse[MessageResponse],
)
async def send_attachment(
    channel_id: UUID, principal: CurrentPrincipal, db: DbSession,
    file: Annotated[UploadFile, File()], content: Annotated[str | None, Form()] = None,
):
    return DataResponse(data=await ChatService(db).send_attachment(principal, channel_id, file, content))


@router.get("/attachments/{attachment_id}/download", response_class=RedirectResponse)
async def download_attachment(attachment_id: UUID, principal: CurrentPrincipal, db: DbSession):
    url = await ChatService(db).attachment_download_url(principal, attachment_id)
    return RedirectResponse(url=url, status_code=307)


@router.patch("/messages/{message_id}", response_model=DataResponse[MessageResponse])
async def edit(message_id: UUID, request: MessageRequest, principal: CurrentPrincipal, db: DbSession):
    return DataResponse(data=await ChatService(db).edit(principal, message_id, request))


@router.delete("/messages/{message_id}", status_code=204, response_class=Response)
async def delete(message_id: UUID, principal: CurrentPrincipal, db: DbSession):
    await ChatService(db).delete(principal, message_id)
    return Response(status_code=204)


@router.put("/messages/{message_id}/reactions/{emoji}", response_model=DataResponse[list[ReactionSummaryResponse]])
async def add_reaction(
    message_id: UUID, emoji: Annotated[str, Path(min_length=1, max_length=32)],
    principal: CurrentPrincipal, db: DbSession,
):
    return DataResponse(data=await ChatService(db).add_reaction(principal, message_id, emoji))


@router.delete("/messages/{message_id}/reactions/{emoji}", status_code=204, response_class=Response)
async def remove_reaction(
    message_id: UUID, emoji: Annotated[str, Path(min_length=1, max_length=32)],
    principal: CurrentPrincipal, db: DbSession,
):
    await ChatService(db).remove_reaction(principal, message_id, emoji)
    return Response(status_code=204)
