from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from app.schemas.tenant import TenantResponse
from app.schemas.company import CompanyResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserMeResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    email: str
    is_superuser: bool
    tenant: TenantResponse
    companies: List[CompanyResponse] = []
    permissions: List[str] = []
