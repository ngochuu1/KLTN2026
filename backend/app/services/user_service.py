from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.security import hash_password, verify_password
from app.repositories.auth_session_repository import AuthSessionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import ChangePasswordRequest, UserProfileResponse, UserUpdateRequest
from app.services.auth_service import AuthService, Principal


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.auth = AuthService(db)
        self.users = UserRepository(db)
        self.sessions = AuthSessionRepository(db)

    async def get_profile(self, principal: Principal) -> UserProfileResponse:
        return UserProfileResponse.model_validate(principal.user)

    async def update_profile(self, principal: Principal, request: UserUpdateRequest) -> UserProfileResponse:
        async with self.db.begin():
            current = await self.auth.load_principal(principal.user.id, principal.session.id)
            user = await self.users.update_full_name(current.user, request.full_name)
            result = UserProfileResponse.model_validate(user)
        return result

    async def change_password(self, principal: Principal, request: ChangePasswordRequest) -> None:
        async with self.db.begin():
            current = await self.auth.load_principal(principal.user.id, principal.session.id)
            if not await verify_password(request.current_password.get_secret_value(), current.user.password_hash):
                raise AppError(400, "CURRENT_PASSWORD_INCORRECT", "Mật khẩu hiện tại không chính xác")
            if await verify_password(request.new_password.get_secret_value(), current.user.password_hash):
                raise AppError(400, "NEW_PASSWORD_SAME_AS_CURRENT", "Mật khẩu mới phải khác mật khẩu hiện tại")
            new_hash = await hash_password(request.new_password.get_secret_value())
            await self.users.update_password_hash(current.user, new_hash)
            await self.sessions.revoke_other_sessions(current.user.id, current.session.id, now=datetime.now(UTC))
