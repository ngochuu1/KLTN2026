from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator
from pydantic_core import PydanticCustomError

from app.schemas.fields import ExistingPassword, FullName, NormalizedEmail, Password
from app.schemas.user import UserPublic


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    full_name: FullName
    email: NormalizedEmail
    password: Password
    confirm_password: Password

    @field_validator("confirm_password")
    @classmethod
    def confirmation_matches(cls, value: Password, info: ValidationInfo) -> Password:
        password = info.data.get("password")
        if password is not None and value.get_secret_value() != password.get_secret_value():
            raise PydanticCustomError("PASSWORD_CONFIRMATION_MISMATCH", "Password confirmation does not match")
        return value


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    email: NormalizedEmail
    password: ExistingPassword


class RegisterResponse(UserPublic):
    created_at: datetime


class RefreshResponse(BaseModel):
    access_token: str = Field(repr=False)
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(gt=0)


class TokenResponse(RefreshResponse):
    user: UserPublic
