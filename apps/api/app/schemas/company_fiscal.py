import uuid
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class FiscalCompanyConfigBase(BaseModel):
    environment: str = Field("HOMOLOGATION", description="HOMOLOGATION ou PRODUCTION")
    tax_regime: str = Field("SIMPLES_NACIONAL", description="SIMPLES_NACIONAL, MEI, REGIME_NORMAL")
    crt: int = Field(1, ge=1, le=4, description="1-Simples, 2-Simples Excesso, 3-Regime Normal, 4-MEI")
    state_tax_number: Optional[str] = Field(None, description="Inscrição Estadual (IE)")
    municipal_tax_number: Optional[str] = Field(None, description="Inscrição Municipal (IM)")
    ibge_city_code: Optional[str] = Field(None, description="Código IBGE do Município (7 dígitos)")

    nfc_csc_id: Optional[str] = Field(None, description="ID do token CSC da NFC-e")
    nfc_csc_secret: Optional[str] = Field(None, description="Segredo do token CSC da NFC-e")

    nfse_provider: Optional[str] = Field("NACIONAL", description="Provedor de NFS-e")
    nfse_environment: str = Field("HOMOLOGATION", description="HOMOLOGATION ou PRODUCTION")

    contingency_mode: str = Field("NONE", description="NONE, OFFLINE_NFC, EPEC")
    contingency_reason: Optional[str] = Field(None, description="Motivo do acionamento da contingência")

    @field_validator("ibge_city_code")
    def validate_ibge(cls, v: Optional[str]) -> Optional[str]:
        if v:
            clean = v.strip()
            if len(clean) != 7 or not clean.isdigit():
                raise ValueError("Código IBGE deve conter exatamente 7 dígitos numéricos.")
            return clean
        return v


class FiscalCompanyConfigCreate(FiscalCompanyConfigBase):
    pass


class FiscalCompanyConfigUpdate(FiscalCompanyConfigBase):
    pass


class FiscalCompanyConfigResponse(FiscalCompanyConfigBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    company_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FiscalSeriesBase(BaseModel):
    doc_model: str = Field(..., description="Modelo do Documento: '55' (NF-e), '65' (NFC-e), 'NFS'")
    series: int = Field(1, ge=1, description="Número da Série")
    current_number: int = Field(0, ge=0, description="Último número de nota autorizado")
    environment: str = Field("HOMOLOGATION", description="HOMOLOGATION ou PRODUCTION")
    is_active: bool = True


class FiscalSeriesCreate(FiscalSeriesBase):
    pass


class FiscalSeriesUpdate(BaseModel):
    current_number: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class FiscalSeriesResponse(FiscalSeriesBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    company_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FiscalCertificateMetadataResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    filename: str
    subject_cn: str
    subject_cnpj: Optional[str] = None
    issuer: str
    serial_number: str
    valid_from: datetime
    valid_until: datetime
    is_expired: bool
    is_valid: bool
    days_until_expiration: int
    is_active: bool

    class Config:
        from_attributes = True
