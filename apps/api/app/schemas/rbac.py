from datetime import datetime
from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class PermissionResponse(BaseModel):
    id: UUID
    code: str
    name: str
    module: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    tenant_id: Optional[UUID] = None
    permission_ids: List[UUID] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[UUID]] = None


class RoleResponse(RoleBase):
    id: UUID
    tenant_id: Optional[UUID] = None
    is_system: bool
    permissions: List[PermissionResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
