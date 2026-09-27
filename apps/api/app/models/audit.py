import uuid
from typing import TYPE_CHECKING, Optional
from datetime import datetime
from sqlalchemy import String, UUID, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.company import Company
    from app.models.user import User


class AuditLog(Base, TimestampMixin):
    """
    Registro imutável de audit trail para rastreabilidade de operações sensíveis.
    """
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )  # 'CREATE', 'UPDATE', 'DELETE', 'CANCEL', 'PRICE_CHANGE', 'STOCK_ADJUSTMENT', 'CASH_CLOSE'
    entity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )  # 'product', 'sale', 'stock', 'cash', 'user', 'role', 'purchase', 'finance'
    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )
    before_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string do estado anterior
    after_data: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON string do novo estado
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    company: Mapped["Company"] = relationship("Company")
    user: Mapped["User"] = relationship("User")
