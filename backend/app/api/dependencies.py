from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.db.session import get_db
from app.services.auth_service import AuthService, Principal

DbSession = Annotated[AsyncSession, Depends(get_db)]
_bearer = HTTPBearer(auto_error=False)


async def get_current_principal(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Principal:
    if credentials is None:
        raise AppError(401, "AUTHENTICATION_REQUIRED", "Yêu cầu đăng nhập")
    return await AuthService(db).authenticate(credentials.credentials)


CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]
