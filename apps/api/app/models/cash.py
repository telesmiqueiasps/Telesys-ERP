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


class CashRegisterStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class CashMovementType(str, enum.Enum):
    OPENING = "OPENING"     # Saldo inicial de abertura (Fundo de troco)
    SUPPLY = "SUPPLY"       # Suprimento (Entrada manual de dinheiro)
    BLEED = "BLEED"         # Sangria (Retirada manual de dinheiro)
    CLOSING = "CLOSING"     # Fechamento de caixa
    SALE = "SALE"           # Entrada por venda do PDV


class PaymentMethod(str, enum.Enum):
    MONEY = "MONEY"             # Dinheiro
    PIX = "PIX"                 # PIX
    CREDIT_CARD = "CREDIT_CARD" # Cartão de Crédito
    DEBIT_CARD = "DEBIT_CARD"   # Cartão de Débito
    BOLETO = "BOLETO"           # Boleto Bancário
    OTHER = "OTHER"             # Outros


class CashRegister(Base, TimestampMixin):
    """
    Representa uma sessão de caixa aberta por um operador.
    """
    __tablename__ = "cash_registers"

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
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    initial_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    final_declared_balance: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )
    difference_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )
    status: Mapped[CashRegisterStatus] = mapped_column(
        Enum(CashRegisterStatus, native_enum=False),
        default=CashRegisterStatus.OPEN,
        nullable=False,
        index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    company: Mapped["Company"] = relationship("Company")
    user: Mapped["User"] = relationship("User")
    movements: Mapped[List["CashMovement"]] = relationship(
        "CashMovement",
        back_populates="cash_register",
        cascade="all, delete-orphan",
        order_by="CashMovement.created_at.asc()"
    )


class CashMovement(Base, TimestampMixin):
    """
    Movimentação individual dentro de uma sessão de caixa.
    """
    __tablename__ = "cash_movements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    cash_register_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cash_registers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
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
    movement_type: Mapped[CashMovementType] = mapped_column(
        Enum(CashMovementType, native_enum=False),
        nullable=False,
        index=True
    )
    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, native_enum=False),
        default=PaymentMethod.MONEY,
        nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    cash_register: Mapped["CashRegister"] = relationship("CashRegister", back_populates="movements")
    user: Mapped["User"] = relationship("User")
