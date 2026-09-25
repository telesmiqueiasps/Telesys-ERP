from datetime import datetime
from uuid import UUID
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.models.cash import CashRegisterStatus, CashMovementType, PaymentMethod


# Movement Schemas
class CashMovementBase(BaseModel):
    movement_type: CashMovementType
    payment_method: PaymentMethod = PaymentMethod.MONEY
    amount: Decimal
    description: Optional[str] = None


class CashMovementCreate(CashMovementBase):
    pass


class CashMovementResponse(CashMovementBase):
    id: UUID
    cash_register_id: UUID
    tenant_id: UUID
    company_id: UUID
    user_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Cash Register Schemas
class CashRegisterOpenInput(BaseModel):
    initial_balance: Decimal = Decimal("0.00")
    notes: Optional[str] = None


class CashRegisterCloseInput(BaseModel):
    final_declared_balance: Decimal
    notes: Optional[str] = None


class CashRegisterResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    company_id: UUID
    user_id: UUID
    opened_at: datetime
    closed_at: Optional[datetime] = None
    initial_balance: Decimal
    current_balance: Decimal
    final_declared_balance: Optional[Decimal] = None
    difference_amount: Optional[Decimal] = None
    status: CashRegisterStatus
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CashRegisterDetailResponse(CashRegisterResponse):
    user_name: Optional[str] = None
    movements: List[CashMovementResponse] = []

    model_config = ConfigDict(from_attributes=True)
