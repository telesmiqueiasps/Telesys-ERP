import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, UUID, ForeignKey, Numeric, Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.company import Company
    from app.models.user import User
    from app.models.customer import Supplier
    from app.models.product import Product


class PurchaseStatus(str, enum.Enum):
    RECEIVED = "RECEIVED"
    PENDING = "PENDING"
    CANCELED = "CANCELED"


class Purchase(Base, TimestampMixin):
    """
    Registro de Pedido de Compra / Entrada de Mercadoria por NF ou Pedido.
    """
    __tablename__ = "purchases"

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
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=PurchaseStatus.RECEIVED.value,
        index=True
    )
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    discount_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Identificação NF-e de Entrada (Modelo 55)
    access_key: Mapped[str | None] = mapped_column(String(44), nullable=True, index=True)
    nfe_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    nfe_series: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_xml: Mapped[str | None] = mapped_column(Text, nullable=True)
    import_status: Mapped[str] = mapped_column(String(30), nullable=False, default="CONFIRMED")  # DRAFT_PREVIEW, CONFIRMED

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    company: Mapped["Company"] = relationship("Company")
    supplier: Mapped["Supplier | None"] = relationship("Supplier")
    user: Mapped["User"] = relationship("User")
    items: Mapped[List["PurchaseItem"]] = relationship(
        "PurchaseItem",
        back_populates="purchase",
        cascade="all, delete-orphan"
    )


class PurchaseItem(Base, TimestampMixin):
    """
    Itens pertencentes a uma compra/entrada de estoque.
    """
    __tablename__ = "purchase_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    purchase_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchases.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    item_number: Mapped[int] = mapped_column(nullable=False, default=1)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_code: Mapped[str] = mapped_column(String(20), nullable=False, default="UN")
    quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total_cost: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    # De-para e conversão de unidades do XML de fornecedor
    vendor_product_code: Mapped[str | None] = mapped_column(String(60), nullable=True)
    unit_conversion_factor: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=1.0)
    tax_details_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    purchase: Mapped["Purchase"] = relationship("Purchase", back_populates="items")
    product: Mapped["Product"] = relationship("Product")
