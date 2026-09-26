from enum import StrEnum


class AccountStatus(StrEnum):
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"


class SystemRole(StrEnum):
    USER = "USER"
    ADMIN = "ADMIN"


class WorkspaceRole(StrEnum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class InvitationStatus(StrEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    REVOKED = "REVOKED"


class ChannelType(StrEnum):
    TEXT = "TEXT"
    STUDY_ROOM = "STUDY_ROOM"
