from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, EmailStr
from app.schemas.license import LicenseResponse


class TenantAdminSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    document: Optional[str] = None
    is_active: bool
    created_at: datetime
    companies_count: int = 0
    users_count: int = 0
    devices_count: int = 0
    license: Optional[LicenseResponse] = None


class TenantCreateInput(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    document: Optional[str] = Field(None, max_length=20)
    company_name: str = Field(..., min_length=2, max_length=255)
    trade_name: Optional[str] = None
    cnpj: Optional[str] = None
    admin_name: str = Field(..., min_length=2, max_length=100)
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=6, max_length=100)
    plan_name: str = Field("PRO", max_length=50)
    max_devices: int = Field(5, ge=1, le=100)


class TenantStatusUpdate(BaseModel):
    is_active: bool


class LicenseUpdateInput(BaseModel):
    plan_name: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=20)
    max_devices: Optional[int] = Field(None, ge=1, le=100)
    offline_grace_days: Optional[int] = Field(None, ge=1, le=90)
    expires_at: Optional[datetime] = None


class SuperAdminMetrics(BaseModel):
    total_tenants: int
    active_tenants: int
    blocked_tenants: int
    total_devices: int
    active_devices: int
    estimated_mrr: float
