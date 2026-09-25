from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict


class TenantBase(BaseModel):
    name: str
    document: Optional[str] = None
    is_active: bool = True


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    document: Optional[str] = None
    is_active: Optional[bool] = None


class TenantResponse(TenantBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
