import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.user import User
    from app.models.rbac import Role


class Tenant(Base, TimestampMixin):
    """
    Tenant entity representing a customer organization in the cloud platform.
    All companies, users, and roles belong to a specific tenant.
    """
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    document: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    companies: Mapped[List["Company"]] = relationship(
        "Company", back_populates="tenant", cascade="all, delete-orphan"
    )
    users: Mapped[List["User"]] = relationship(
        "User", back_populates="tenant", cascade="all, delete-orphan"
    )
    roles: Mapped[List["Role"]] = relationship(
        "Role", back_populates="tenant", cascade="all, delete-orphan"
    )
