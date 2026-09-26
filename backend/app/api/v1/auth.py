from fastapi import APIRouter, Request, Response

from app.api.cookies import clear_refresh_cookie, set_refresh_cookie
from app.api.dependencies import CurrentPrincipal, DbSession
from app.core.config import get_settings
from app.schemas.auth import LoginRequest, RefreshResponse, RegisterRequest, RegisterResponse, TokenResponse
from app.schemas.common import DataResponse, ErrorResponse
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth", tags=["auth"],
    responses={status: {"model": ErrorResponse} for status in (401, 403, 409, 422)},
)


@router.post("/register", status_code=201, response_model=DataResponse[RegisterResponse])
async def register(request: RegisterRequest, db: DbSession) -> DataResponse[RegisterResponse]:
    return DataResponse(data=await AuthService(db).register(request))


@router.post("/login", response_model=DataResponse[TokenResponse])
async def login(request: LoginRequest, response: Response, db: DbSession) -> DataResponse[TokenResponse]:
    result = await AuthService(db).login(request)
    set_refresh_cookie(response, result.refresh_token, result.refresh_expires_at)
    return DataResponse(data=result.data)


@router.post("/refresh", response_model=DataResponse[RefreshResponse])
async def refresh(request: Request, response: Response, db: DbSession) -> DataResponse[RefreshResponse]:
    token = request.cookies.get(get_settings().refresh_cookie_name)
    result = await AuthService(db).refresh(token)
    set_refresh_cookie(response, result.refresh_token, result.refresh_expires_at)
    return DataResponse(data=result.data)


@router.post("/logout", status_code=204, response_class=Response)
async def logout(principal: CurrentPrincipal, db: DbSession) -> Response:
    await AuthService(db).logout(principal)
    response = Response(status_code=204)
    clear_refresh_cookie(response)
    return response
