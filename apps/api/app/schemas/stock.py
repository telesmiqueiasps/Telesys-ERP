from datetime import datetime
from uuid import UUID
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.schemas.product import ProductResponse
from app.schemas.user import UserResponse


class StockMovementCreate(BaseModel):
    company_id: UUID
    product_id: UUID
    movement_type: str  # ENTRADA_NF, SAIDA_VENDA, AJUSTE_ENTRADA, AJUSTE_SAIDA, ESTORNO
    quantity: Decimal
    unit_cost: Optional[Decimal] = None
    reference_doc: Optional[str] = None
    notes: Optional[str] = None


class StockMovementResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    company_id: UUID
    product_id: UUID
    user_id: UUID
    movement_type: str
    quantity: Decimal
    previous_qty: Decimal
    new_qty: Decimal
    unit_cost: Optional[Decimal] = None
    reference_doc: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StockMovementDetailResponse(StockMovementResponse):
    product: Optional[ProductResponse] = None
    user: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)
