import uuid
import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Numeric, DateTime, Enum, ForeignKey, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.company import Company
    from app.models.user import User
    from app.models.customer import Customer
    from app.models.cash import CashRegister
    from app.models.product import Product


class SaleStatus(str, enum.Enum):
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"


class Sale(Base, TimestampMixin):
    """
    Venda efetuada no PDV ou ERP.
    """
    __tablename__ = "sales"

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
    cash_register_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cash_registers.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # Ex: VND-000001
    status: Mapped[SaleStatus] = mapped_column(
        Enum(SaleStatus, native_enum=False),
        default=SaleStatus.COMPLETED,
        nullable=False,
        index=True
    )

    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    company: Mapped["Company"] = relationship("Company")
    cash_register: Mapped[Optional["CashRegister"]] = relationship("CashRegister")
    customer: Mapped[Optional["Customer"]] = relationship("Customer")
    user: Mapped["User"] = relationship("User")

    items: Mapped[List["SaleItem"]] = relationship(
        "SaleItem",
        back_populates="sale",
        cascade="all, delete-orphan",
        order_by="SaleItem.item_number.asc()"
    )
    payments: Mapped[List["SalePayment"]] = relationship(
        "SalePayment",
        back_populates="sale",
        cascade="all, delete-orphan"
    )


class SaleItem(Base, TimestampMixin):
    """
    Item pertencente a uma venda.
    """
    __tablename__ = "sale_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    sale_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sales.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    item_number: Mapped[int] = mapped_column(nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_code: Mapped[str] = mapped_column(String(10), default="UN", nullable=False)
    
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    ncm: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    cest: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Relationships
    sale: Mapped["Sale"] = relationship("Sale", back_populates="items")
    product: Mapped["Product"] = relationship("Product")


class SalePayment(Base, TimestampMixin):
    """
    Forma de pagamento utilizada em uma venda (pode haver múltiplas).
    """
    __tablename__ = "sale_payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    sale_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sales.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False) # MONEY, PIX, CREDIT_CARD, etc
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    change_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False) # Troco

    # Relationships
    sale: Mapped["Sale"] = relationship("Sale", back_populates="payments")
