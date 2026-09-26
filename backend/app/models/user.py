from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Enum, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.core.normalization import normalize_email
from app.db.base import Base
from app.models.enums import AccountStatus, SystemRole


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("email = lower(btrim(email))", name="ck_users_email_normalized"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus, native_enum=False, create_constraint=True, name="ck_users_status"),
        nullable=False, default=AccountStatus.ACTIVE, server_default="ACTIVE",
    )
    system_role: Mapped[SystemRole] = mapped_column(
        Enum(SystemRole, native_enum=False, create_constraint=True, name="ck_users_system_role"),
        nullable=False, default=SystemRole.USER, server_default="USER",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now(),
    )

    @validates("email")
    def normalize_email_value(self, key: str, value: str) -> str:
        return normalize_email(value)
