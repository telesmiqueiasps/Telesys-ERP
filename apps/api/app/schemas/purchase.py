from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class PurchaseItemCreate(BaseModel):
    product_id: UUID
    quantity: float = Field(..., gt=0, description="Quantidade comprada")
    unit_cost: float = Field(..., ge=0, description="Custo unitário do produto")


class PurchaseCreate(BaseModel):
    supplier_id: Optional[UUID] = None
    items: List[PurchaseItemCreate] = Field(..., min_items=1, description="Lista de produtos na compra")
    discount_amount: float = Field(default=0.0, ge=0)
    notes: Optional[str] = None


class PurchaseItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    purchase_id: UUID
    product_id: UUID
    item_number: int
    product_name: str
    unit_code: str
    quantity: float
    unit_cost: float
    total_cost: float


class PurchaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    company_id: UUID
    supplier_id: Optional[UUID] = None
    supplier_name: Optional[str] = None
    user_id: UUID
    user_name: Optional[str] = None
    code: str
    status: str
    subtotal: float
    discount_amount: float
    total_amount: float
    notes: Optional[str] = None
    items: List[PurchaseItemResponse] = []
    created_at: datetime
    updated_at: datetime
