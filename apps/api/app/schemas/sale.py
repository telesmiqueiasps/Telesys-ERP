from datetime import datetime
from uuid import UUID
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.models.sale import SaleStatus


class SaleItemCreate(BaseModel):
    product_id: UUID
    quantity: Decimal
    unit_price: Decimal
    discount_amount: Decimal = Decimal("0.00")


class SalePaymentCreate(BaseModel):
    payment_method: str
    amount: Decimal
    change_amount: Decimal = Decimal("0.00")


class SaleCreate(BaseModel):
    customer_id: Optional[UUID] = None
    items: List[SaleItemCreate]
    payments: List[SalePaymentCreate]
    discount_amount: Decimal = Decimal("0.00")
    notes: Optional[str] = None


class SaleItemResponse(BaseModel):
    id: UUID
    sale_id: UUID
    product_id: UUID
    item_number: int
    product_name: str
    unit_code: str
    quantity: Decimal
    unit_price: Decimal
    discount_amount: Decimal
    total_price: Decimal
    ncm: Optional[str] = None
    cest: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SalePaymentResponse(BaseModel):
    id: UUID
    sale_id: UUID
    payment_method: str
    amount: Decimal
    change_amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class SaleResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    company_id: UUID
    cash_register_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    user_id: UUID
    code: str
    status: SaleStatus
    subtotal: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SaleDetailResponse(SaleResponse):
    customer_name: Optional[str] = None
    user_name: Optional[str] = None
    items: List[SaleItemResponse] = []
    payments: List[SalePaymentResponse] = []

    model_config = ConfigDict(from_attributes=True)
