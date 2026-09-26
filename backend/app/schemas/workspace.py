from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, StringConstraints, model_validator

from app.models.enums import InvitationStatus, WorkspaceRole

WorkspaceName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class WorkspaceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class WorkspaceCreateRequest(WorkspaceRequest):
    name: WorkspaceName
    description: str | None = None


class WorkspaceUpdateRequest(WorkspaceRequest):
    name: WorkspaceName | None = None
    description: str | None = None

    @model_validator(mode="after")
    def validate_patch(self):
        if not self.model_fields_set or ("name" in self.model_fields_set and self.name is None):
            raise ValueError("Supply name or description; name cannot be null")
        return self


class InvitationCreateRequest(WorkspaceRequest):
    invitee_user_id: UUID | None = None
    expires_at: AwareDatetime | None = None


class MemberRoleRequest(WorkspaceRequest):
    role: str


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    role: WorkspaceRole


class MemberResponse(BaseModel):
    user_id: UUID
    full_name: str
    email: str
    role: WorkspaceRole
    joined_at: datetime


class InvitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    workspace_id: UUID
    invitee_user_id: UUID | None
    status: InvitationStatus
    expires_at: datetime | None
    created_at: datetime


class InvitationCreatedResponse(InvitationResponse):
    token: str


class InvitationPreviewResponse(BaseModel):
    workspace_id: UUID
    name: str
    description: str | None
    expires_at: datetime | None
