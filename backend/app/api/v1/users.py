from fastapi import APIRouter, Response

from app.api.dependencies import CurrentPrincipal, DbSession
from app.schemas.common import DataResponse, ErrorResponse
from app.schemas.user import ChangePasswordRequest, UserProfileResponse, UserUpdateRequest
from app.services.user_service import UserService

router = APIRouter(
    prefix="/users", tags=["users"],
    responses={status: {"model": ErrorResponse} for status in (400, 401, 403, 422)},
)


@router.get("/me", response_model=DataResponse[UserProfileResponse])
async def get_me(principal: CurrentPrincipal, db: DbSession) -> DataResponse[UserProfileResponse]:
    return DataResponse(data=await UserService(db).get_profile(principal))


@router.patch("/me", response_model=DataResponse[UserProfileResponse])
async def update_me(
    request: UserUpdateRequest, principal: CurrentPrincipal, db: DbSession,
) -> DataResponse[UserProfileResponse]:
    return DataResponse(data=await UserService(db).update_profile(principal, request))


@router.post("/me/change-password", status_code=204, response_class=Response)
async def change_password(request: ChangePasswordRequest, principal: CurrentPrincipal, db: DbSession) -> Response:
    await UserService(db).change_password(principal, request)
    return Response(status_code=204)
