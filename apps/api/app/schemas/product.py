from datetime import datetime
from uuid import UUID
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


# Category Schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class CategoryCreate(CategoryBase):
    tenant_id: Optional[UUID] = None
    company_id: Optional[UUID] = None


class CategoryResponse(CategoryBase):
    id: UUID
    tenant_id: UUID
    company_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Unit Schemas
class UnitBase(BaseModel):
    code: str
    name: str
    allow_decimal: bool = False


class UnitCreate(UnitBase):
    pass


class UnitResponse(UnitBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


# Barcode Schemas
class BarcodeResponse(BaseModel):
    id: UUID
    barcode: str

    model_config = ConfigDict(from_attributes=True)


# Product Schemas
class ProductBase(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    price: Decimal
    cost: Decimal = Decimal("0.00")
    stock_qty: Decimal = Decimal("0.000")
    min_stock_qty: Decimal = Decimal("0.000")
    ncm: Optional[str] = None
    cest: Optional[str] = None
    is_active: bool = True


class ProductCreate(ProductBase):
    tenant_id: UUID
    company_id: UUID
    category_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    barcodes: List[str] = []


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    cost: Optional[Decimal] = None
    stock_qty: Optional[Decimal] = None
    min_stock_qty: Optional[Decimal] = None
    category_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    ncm: Optional[str] = None
    cest: Optional[str] = None
    is_active: Optional[bool] = None
    barcodes: Optional[List[str]] = None


class ProductResponse(ProductBase):
    id: UUID
    tenant_id: UUID
    company_id: UUID
    category_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductDetailResponse(ProductResponse):
    category: Optional[CategoryResponse] = None
    unit: Optional[UnitResponse] = None
    barcodes: List[BarcodeResponse] = []

    model_config = ConfigDict(from_attributes=True)
