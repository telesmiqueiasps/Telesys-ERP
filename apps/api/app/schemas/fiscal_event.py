import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class FiscalCancelRequest(BaseModel):
    nfe_id: uuid.UUID
    justification: str = Field(..., min_length=15, max_length=255, example="Cancelamento solicitado pelo cliente antes da entrega.")


class FiscalCceRequest(BaseModel):
    nfe_id: uuid.UUID
    correction_text: str = Field(..., min_length=15, max_length=1000, example="Correção da descrição da marca do item 1 para Marca X.")


class FiscalInutilizationRequest(BaseModel):
    company_id: uuid.UUID
    model: str = Field("55", description="55=NF-e, 65=NFC-e")
    series: int = Field(1, ge=1)
    year: int = Field(..., ge=2020, le=2050, example=2026)
    start_number: int = Field(..., ge=1)
    end_number: int = Field(..., ge=1)
    justification: str = Field(..., min_length=15, max_length=255, example="Inutilização de numeração devido a falha técnica no emissor local.")


class FiscalEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    company_id: uuid.UUID
    nfe_id: Optional[uuid.UUID] = None
    access_key: str
    event_type: str
    event_name: str
    seq_number: int
    justification_or_correction: str
    protocol_number: Optional[str] = None
    sefaz_status_code: Optional[int] = None
    sefaz_reason: Optional[str] = None
    registered_at: Optional[datetime] = None
    created_at: datetime


class FiscalInutilizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    company_id: uuid.UUID
    model: str
    series: int
    year: int
    start_number: int
    end_number: int
    justification: str
    protocol_number: Optional[str] = None
    sefaz_status_code: Optional[int] = None
    sefaz_reason: Optional[str] = None
    registered_at: Optional[datetime] = None
    created_at: datetime
