from typing import List, Optional
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field


# --- Categorias Financeiras ---
class FinancialCategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    type: str = Field(default="DESPESA", description="'DESPESA' ou 'RECEITA'")
    color: Optional[str] = "#64748b"
    is_active: bool = True


class FinancialCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    company_id: UUID
    name: str
    type: str
    color: Optional[str] = None
    is_active: bool
    created_at: datetime


# --- Contas a Pagar ---
class AccountPayableCreate(BaseModel):
    description: str = Field(..., min_length=2, max_length=255)
    amount: float = Field(..., gt=0)
    due_date: date
    supplier_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    purchase_id: Optional[UUID] = None
    notes: Optional[str] = None


class AccountPayablePayInput(BaseModel):
    paid_amount: float = Field(..., gt=0)
    payment_method: str = Field(..., description="'MONEY', 'PIX', 'CREDIT_CARD', 'BOLETO', etc.")
    paid_at: Optional[datetime] = None


class AccountPayableResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    company_id: UUID
    supplier_id: Optional[UUID] = None
    supplier_name: Optional[str] = None
    category_id: Optional[UUID] = None
    category_name: Optional[str] = None
    purchase_id: Optional[UUID] = None
    description: str
    amount: float
    paid_amount: float
    due_date: date
    paid_at: Optional[datetime] = None
    status: str
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime


# --- Contas a Receber ---
class AccountReceivableCreate(BaseModel):
    description: str = Field(..., min_length=2, max_length=255)
    amount: float = Field(..., gt=0)
    due_date: date
    customer_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    sale_id: Optional[UUID] = None
    notes: Optional[str] = None


class AccountReceivableReceiveInput(BaseModel):
    received_amount: float = Field(..., gt=0)
    payment_method: str = Field(..., description="'MONEY', 'PIX', 'CREDIT_CARD', 'BOLETO', etc.")
    received_at: Optional[datetime] = None


class AccountReceivableResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    company_id: UUID
    customer_id: Optional[UUID] = None
    customer_name: Optional[str] = None
    category_id: Optional[UUID] = None
    category_name: Optional[str] = None
    sale_id: Optional[UUID] = None
    description: str
    amount: float
    received_amount: float
    due_date: date
    received_at: Optional[datetime] = None
    status: str
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime


# --- Extrato / Movimentação Financeira ---
class FinancialMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    company_id: UUID
    user_id: UUID
    user_name: Optional[str] = None
    category_id: Optional[UUID] = None
    category_name: Optional[str] = None
    movement_type: str
    amount: float
    description: str
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    created_at: datetime


# --- Dashboard Resumo Financeiro ---
class FinancialSummaryResponse(BaseModel):
    total_receivable_pending: float
    total_payable_pending: float
    total_overdue: float
    forecast_balance: float
