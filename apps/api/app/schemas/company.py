from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CompanyBase(BaseModel):
    name: str
    trade_name: Optional[str] = None
    cnpj: Optional[str] = None
    state_registration: Optional[str] = None
    is_active: bool = True


class CompanyCreate(CompanyBase):
    tenant_id: UUID


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    trade_name: Optional[str] = None
    cnpj: Optional[str] = None
    state_registration: Optional[str] = None
    is_active: Optional[bool] = None


class CompanyResponse(CompanyBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
