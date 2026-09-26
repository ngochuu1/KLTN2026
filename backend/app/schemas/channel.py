from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

from app.models.enums import ChannelType

ChannelName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class ChannelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class ChannelCreateRequest(ChannelRequest):
    name: ChannelName
    description: str | None = None
    type: str


class ChannelUpdateRequest(ChannelRequest):
    name: ChannelName | None = None
    description: str | None = None

    @model_validator(mode="after")
    def validate_patch(self):
        if not self.model_fields_set or ("name" in self.model_fields_set and self.name is None):
            raise ValueError("Supply name or description; name cannot be null")
        return self


class ChannelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    description: str | None
    type: ChannelType
    is_default: bool
    created_at: datetime
    updated_at: datetime
