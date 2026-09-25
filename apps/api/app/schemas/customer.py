from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CustomerBase(BaseModel):
    name: str
    trade_name: Optional[str] = None
    document: Optional[str] = None  # CPF / CNPJ
    phone: Optional[str] = None
    email: Optional[str] = None
    
    # Address info
    address_street: Optional[str] = None
    address_number: Optional[str] = None
    address_neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    
    notes: Optional[str] = None
    is_active: bool = True


class CustomerCreate(CustomerBase):
    tenant_id: Optional[UUID] = None
    company_id: Optional[UUID] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    trade_name: Optional[str] = None
    document: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address_street: Optional[str] = None
    address_number: Optional[str] = None
    address_neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerResponse(CustomerBase):
    id: UUID
    tenant_id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
