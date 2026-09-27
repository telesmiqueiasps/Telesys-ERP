from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    company_id: UUID
    user_id: UUID
    user_name: Optional[str] = None
    action: str
    entity: str
    entity_id: Optional[UUID] = None
    before_data: Optional[str] = None
    after_data: Optional[str] = None
    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
