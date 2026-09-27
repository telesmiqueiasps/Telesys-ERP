from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class LicenseActivateInput(BaseModel):
    license_key: str = Field(..., min_length=5, max_length=100)
    device_id: str = Field(..., min_length=5, max_length=100)
    device_name: str = Field(..., min_length=2, max_length=100)
    os_info: Optional[str] = "Windows"
    app_version: Optional[str] = "1.0.0"


class LicenseHeartbeatInput(BaseModel):
    license_key: str
    device_id: str


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    license_id: UUID
    device_id: str
    device_name: str
    os_info: Optional[str] = None
    app_version: Optional[str] = None
    status: str
    last_heartbeat_at: Optional[datetime] = None
    created_at: datetime


class LicenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    license_key: str
    plan_name: str
    status: str
    max_devices: int
    expires_at: Optional[datetime] = None
    offline_grace_days: int
    active_devices_count: int = 0
    devices: List[DeviceResponse] = []
    created_at: datetime
