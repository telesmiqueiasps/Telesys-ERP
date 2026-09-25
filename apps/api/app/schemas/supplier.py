from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict


class SupplierBase(BaseModel):
    name: str  # Razao Social
    trade_name: Optional[str] = None  # Nome Fantasia
    document: Optional[str] = None  # CNPJ / CPF
    state_registration: Optional[str] = None  # IE
    phone: Optional[str] = None
    email: Optional[str] = None
    contact_person: Optional[str] = None
    
    # Address info
    address_street: Optional[str] = None
    address_number: Optional[str] = None
    address_neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    
    notes: Optional[str] = None
    is_active: bool = True


class SupplierCreate(SupplierBase):
    tenant_id: Optional[UUID] = None
    company_id: Optional[UUID] = None


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    trade_name: Optional[str] = None
    document: Optional[str] = None
    state_registration: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    contact_person: Optional[str] = None
    address_street: Optional[str] = None
    address_number: Optional[str] = None
    address_neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierResponse(SupplierBase):
    id: UUID
    tenant_id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
