import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, UUID, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.company import Company
    from app.models.user import User
    from app.models.product import Product


class StockMovementType(str, enum.Enum):
    ENTRADA_NF = "ENTRADA_NF"
    SAIDA_VENDA = "SAIDA_VENDA"
    AJUSTE_ENTRADA = "AJUSTE_ENTRADA"
    AJUSTE_SAIDA = "AJUSTE_SAIDA"
    ESTORNO = "ESTORNO"


class StockMovement(Base, TimestampMixin):
    """
    Append-Only immutable audit log of stock movements (Rule of Gold: Stock Audit Trail).
    """
    __tablename__ = "stock_movements"

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
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    movement_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    previous_qty: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    new_qty: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    unit_cost: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    reference_doc: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    company: Mapped["Company"] = relationship("Company")
    product: Mapped["Product"] = relationship("Product")
    user: Mapped["User"] = relationship("User")
