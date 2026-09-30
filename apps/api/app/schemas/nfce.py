import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class NfceEmitResponse(BaseModel):
    nfe_id: uuid.UUID
    sale_id: Optional[uuid.UUID] = None
    access_key: str
    number: int
    series: int
    model: str = "65"
    status: str
    protocol_number: Optional[str] = None
    qr_code_url: Optional[str] = None
    url_chave: Optional[str] = None
    danfe_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DanfeNfceResponse(BaseModel):
    nfe_id: uuid.UUID
    access_key: str
    number: int
    series: int
    status: str
    html_content: str
