import uuid
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class NfseCreateRequest(BaseModel):
    company_id: uuid.UUID
    customer_id: Optional[uuid.UUID] = None
    service_code_lc116: str = Field(..., description="Código do Serviço conforme LC 116/03 (ex: '07.02', '17.06')")
    national_tax_code: Optional[str] = Field(None, description="Código de Tributação Nacional cTribNac")
    service_description: str = Field(..., min_length=5, description="Descrição detalhada do serviço prestado")
    municipality_ibge: str = Field(..., min_length=7, max_length=7, description="Código IBGE do município da prestação (7 dígitos)")
    iss_taxation_type: int = Field(1, description="1=Devido no município, 2=Retido, etc.")

    # Tomador (Customer snapshot)
    taker_document: str = Field(..., description="CPF ou CNPJ do tomador")
    taker_name: str = Field(..., description="Nome / Razão Social do tomador")
    taker_email: Optional[str] = None
    taker_uf: Optional[str] = None

    # Valores
    service_amount: float = Field(..., gt=0, description="Valor bruto dos serviços (vServ)")
    deductions_amount: float = Field(0.0, ge=0, description="Deduções (vDed)")
    discount_unconditional: float = Field(0.0, ge=0)
    discount_conditional: float = Field(0.0, ge=0)

    iss_rate: float = Field(..., ge=0, description="Alíquota do ISS em porcentagem (ex: 2.0 para 2%)")
    iss_withheld: bool = Field(False, description="ISS retido pelo tomador?")

    # Retenções Federais
    pis_retained: float = Field(0.0, ge=0)
    cofins_retained: float = Field(0.0, ge=0)
    csll_retained: float = Field(0.0, ge=0)
    ir_retained: float = Field(0.0, ge=0)
    inss_retained: float = Field(0.0, ge=0)

    provider_type: Optional[str] = Field("NATIONAL", description="NATIONAL, ABRASF_V2, PAULISTANA")


class NfseCancelRequest(BaseModel):
    justification: str = Field(..., min_length=15, description="Justificativa do cancelamento (mínimo 15 caracteres)")
    cancellation_code: Optional[str] = Field("1", description="Código de cancelamento municipal/nacional")


class NfseEmissionResult(BaseModel):
    success: bool
    nfse_id: uuid.UUID
    dps_number: int
    dps_series: str
    nfse_number: Optional[str] = None
    nfse_verification_code: Optional[str] = None
    access_key_national: Optional[str] = None
    protocol_number: Optional[str] = None
    status: str
    sefaz_status_code: Optional[int] = None
    sefaz_reason: Optional[str] = None
    issued_at: Optional[datetime] = None


class NfseResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    company_id: uuid.UUID
    customer_id: Optional[uuid.UUID] = None
    dps_number: int
    dps_series: str
    dps_id: str
    nfse_number: Optional[str] = None
    nfse_verification_code: Optional[str] = None
    access_key_national: Optional[str] = None
    provider_type: str
    status: str
    environment: int
    service_code_lc116: str
    national_tax_code: Optional[str] = None
    service_description: str
    municipality_ibge: str
    taker_document: str
    taker_name: str
    service_amount: float
    iss_rate: float
    iss_amount: float
    iss_withheld: bool
    net_amount: float
    protocol_number: Optional[str] = None
    sefaz_status_code: Optional[int] = None
    sefaz_reason: Optional[str] = None
    issued_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
