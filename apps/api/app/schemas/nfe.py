import uuid
from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, ConfigDict, Field


class NfeItemCreate(BaseModel):
    product_id: Optional[uuid.UUID] = None
    product_code: str = Field(..., max_length=60)
    gtin: str = Field("SEM GTIN", max_length=14)
    description: str = Field(..., max_length=120)
    ncm: str = Field(..., min_length=8, max_length=8)
    cest: Optional[str] = Field(None, max_length=7)
    uCom: str = Field("UN", max_length=6)
    qCom: float = Field(..., gt=0)
    vUnCom: float = Field(..., gt=0)
    vProd: float = Field(..., gt=0)
    
    vFrete: float = Field(0.0, ge=0)
    vSeguro: float = Field(0.0, ge=0)
    vDesc: float = Field(0.0, ge=0)
    vOutro: float = Field(0.0, ge=0)


class NfeDocumentCreate(BaseModel):
    company_id: uuid.UUID
    fiscal_operation_code: str = Field(..., example="VENDA_ESTADO")
    sale_id: Optional[uuid.UUID] = None
    purchase_id: Optional[uuid.UUID] = None

    # Destinatário
    recipient_cnpj_cpf: str = Field(..., min_length=11, max_length=14)
    recipient_name: str = Field(..., max_length=100)
    recipient_ie: Optional[str] = Field(None, max_length=14)
    recipient_email: Optional[str] = Field(None, max_length=100)
    recipient_uf: str = Field(..., min_length=2, max_length=2)
    recipient_is_final_consumer: bool = True
    recipient_is_tax_contributor: bool = False
    recipient_address: Optional[dict] = Field(None, example={
        "xLgr": "Rua Exemplo",
        "nro": "123",
        "xBairro": "Centro",
        "cMun": "3550308",
        "xMun": "São Paulo",
        "UF": "SP",
        "CEP": "01001000"
    })

    # Referências (ex: devolução)
    referenced_nfe_key: Optional[str] = Field(None, min_length=44, max_length=44)

    items: List[NfeItemCreate] = Field(..., min_items=1)


class NfeItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    item_number: int
    product_code: str
    gtin: str
    description: str
    ncm: str
    cest: Optional[str] = None
    cfop: str
    uCom: str
    qCom: float
    vUnCom: float
    vProd: float
    vFrete: float
    vSeguro: float
    vDesc: float
    vOutro: float
    tax_snapshot_json: dict


class NfeDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    company_id: uuid.UUID
    access_key: str
    number: int
    series: int
    model: str
    nature_of_operation: str
    operation_type_nfe: Optional[int] = 1
    purpose: Optional[int] = 1
    issue_type: int
    environment: int
    status: str

    issuer_cnpj: str
    issuer_name: str
    issuer_uf: str
    
    recipient_cnpj_cpf: str
    recipient_name: str
    recipient_uf: str

    vProd: float
    vFrete: float
    vSeguro: float
    vDesc: float
    vOutro: float
    vBC: float
    vICMS: float
    vFCP: float
    vBCST: float
    vST: float
    vIPI: float
    vPIS: float
    vCOFINS: float
    vNF: float

    referenced_nfe_key: Optional[str] = None
    additional_information: Optional[str] = None
    protocol_number: Optional[str] = None
    digest_value: Optional[str] = None
    sefaz_status_code: Optional[int] = None
    sefaz_reason: Optional[str] = None
    authorized_at: Optional[datetime] = None

    items: List[NfeItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
