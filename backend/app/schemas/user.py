from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator
from pydantic_core import PydanticCustomError

from app.models.enums import AccountStatus, SystemRole
from app.schemas.fields import ExistingPassword, FullName, NormalizedEmail, Password


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: NormalizedEmail
    status: AccountStatus
    system_role: SystemRole


class UserProfileResponse(UserPublic):
    created_at: datetime
    updated_at: datetime


class UserUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    full_name: FullName


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    current_password: ExistingPassword
    new_password: Password
    confirm_new_password: Password

    @field_validator("confirm_new_password")
    @classmethod
    def confirmation_matches(cls, value: Password, info: ValidationInfo) -> Password:
        password = info.data.get("new_password")
        if password is not None and value.get_secret_value() != password.get_secret_value():
            raise PydanticCustomError("PASSWORD_CONFIRMATION_MISMATCH", "Password confirmation does not match")
        return value
