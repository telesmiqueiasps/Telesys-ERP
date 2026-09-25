from datetime import datetime
from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict
from app.schemas.rbac import RoleResponse


class UserBase(BaseModel):
    name: str
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    tenant_id: UUID
    password: str
    role_ids: List[UUID] = []


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    role_ids: Optional[List[UUID]] = None


class UserResponse(UserBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserWithRolesResponse(UserResponse):
    roles: List[RoleResponse] = []

    model_config = ConfigDict(from_attributes=True)
