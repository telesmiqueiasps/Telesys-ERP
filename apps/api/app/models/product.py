import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean, UUID, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.company import Company


class ProductCategory(Base, TimestampMixin):
    """
    Product Category (e.g. 'Bebidas', 'Alimentos', 'Higiene').
    """
    __tablename__ = "product_categories"

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
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    products: Mapped[List["Product"]] = relationship("Product", back_populates="category")


class ProductUnit(Base):
    """
    Product Unit of Measurement (e.g., 'UN', 'KG', 'CX', 'LT', 'M').
    """
    __tablename__ = "product_units"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    allow_decimal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    products: Mapped[List["Product"]] = relationship("Product", back_populates="unit")


class ProductBarcode(Base):
    """
    Barcodes associated with a product (EAN-13, EAN-8, Internal Barcode).
    """
    __tablename__ = "product_barcodes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    barcode: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="barcodes")


class Product(Base, TimestampMixin):
    """
    Product entity representing inventory items for ERP and PDV.
    Prices and costs use NUMERIC/Decimal (never float for currency!).
    """
    __tablename__ = "products"

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
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    unit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_units.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    code: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    cost: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    stock_qty: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0.0)
    min_stock_qty: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0.0)
    ncm: Mapped[str | None] = mapped_column(String(10), nullable=True)
    cest: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    category: Mapped["ProductCategory | None"] = relationship("ProductCategory", back_populates="products")
    unit: Mapped["ProductUnit | None"] = relationship("ProductUnit", back_populates="products")
    barcodes: Mapped[List["ProductBarcode"]] = relationship("ProductBarcode", back_populates="product", cascade="all, delete-orphan")
