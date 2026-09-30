import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class ValidationErrorItem(BaseModel):
    field: str
    code: str
    message: str
    official_solution: Optional[str] = None


class PreValidationResult(BaseModel):
    is_valid: bool
    errors: List[ValidationErrorItem]
    warnings: List[ValidationErrorItem] = []


class SefazRejectionCatalogEntry(BaseModel):
    code: int
    official_message: str
    affected_fields: List[str]
    operational_solution: Optional[str] = None


class NfeRejectionLogRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    company_id: uuid.UUID
    nfe_id: uuid.UUID
    access_key: str
    sefaz_code: int
    official_message: str
    affected_fields: Optional[List[str]] = None
    operational_solution: Optional[str] = None
    raw_sefaz_response: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
