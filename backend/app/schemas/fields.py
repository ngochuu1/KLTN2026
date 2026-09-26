from typing import Annotated

from pydantic import AfterValidator, BeforeValidator, EmailStr, Field, SecretStr, StringConstraints

from app.core.normalization import normalize_email


def _strip_email(value: object) -> object:
    return normalize_email(value) if isinstance(value, str) else value


NormalizedEmail = Annotated[
    EmailStr, BeforeValidator(_strip_email), AfterValidator(normalize_email), Field(max_length=254),
]
FullName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Password = Annotated[SecretStr, Field(min_length=8, max_length=128)]
ExistingPassword = Annotated[SecretStr, Field(min_length=1, max_length=128)]
