import uuid
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class ProductFiscalProfileBase(BaseModel):
    ncm: Optional[str] = Field(None, description="NCM com 8 dígitos numéricos")
    cest: Optional[str] = Field(None, description="CEST com 7 dígitos numéricos se houver ST")
    origin: int = Field(0, ge=0, le=8, description="Origem da mercadoria (0-8)")

    gtin_commercial: Optional[str] = Field(None, description="GTIN/EAN comercial")
    gtin_taxable: Optional[str] = Field(None, description="GTIN/EAN tributável")
    unit_commercial: Optional[str] = Field("UN", description="Unidade de medida comercial")
    unit_taxable: Optional[str] = Field("UN", description="Unidade tributável")
    conversion_factor: float = Field(1.0000, gt=0, description="Fator de conversão para unidade tributável")

    cst_csosn: Optional[str] = Field("102", description="CST (Regime Normal) ou CSOSN (Simples Nacional)")
    cfop_default_inside: str = Field("5102", description="CFOP padrão para operações estaduais")
    cfop_default_outside: str = Field("6102", description="CFOP padrão para operações interestaduais")

    icms_rate: float = Field(0.00, ge=0, le=100)
    icms_st_rate: float = Field(0.00, ge=0, le=100)
    fcp_rate: float = Field(0.00, ge=0, le=100)

    ipi_cst: Optional[str] = Field("99", description="CST de IPI")
    ipi_rate: float = Field(0.00, ge=0, le=100)

    pis_cst: Optional[str] = Field("49", description="CST de PIS")
    pis_rate: float = Field(0.00, ge=0, le=100)

    cofins_cst: Optional[str] = Field("49", description="CST de COFINS")
    cofins_rate: float = Field(0.00, ge=0, le=100)

    # Grupo Reforma Tributária RTC (IBS / CBS)
    ibs_cst: Optional[str] = Field("01", description="CST de IBS")
    ibs_rate: float = Field(0.00, ge=0, le=100)
    cbs_cst: Optional[str] = Field("01", description="CST de CBS")
    cbs_rate: float = Field(0.00, ge=0, le=100)

    source_reference: Optional[str] = Field(None, description="Referência legal/base normativa")

    @field_validator("ncm")
    def validate_ncm(cls, v: Optional[str]) -> Optional[str]:
        if v:
            clean_ncm = v.replace(".", "").strip()
            if len(clean_ncm) != 8 or not clean_ncm.isdigit():
                raise ValueError("NCM deve conter exatamente 8 dígitos numéricos.")
            return clean_ncm
        return v

    @field_validator("cest")
    def validate_cest(cls, v: Optional[str]) -> Optional[str]:
        if v:
            clean_cest = v.replace(".", "").strip()
            if len(clean_cest) != 7 or not clean_cest.isdigit():
                raise ValueError("CEST deve conter exatamente 7 dígitos numéricos.")
            return clean_cest
        return v


class ProductFiscalProfileCreate(ProductFiscalProfileBase):
    pass


class ProductFiscalProfileUpdate(ProductFiscalProfileBase):
    pass


class ProductFiscalProfileResponse(ProductFiscalProfileBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    company_id: uuid.UUID
    product_id: uuid.UUID
    effective_from: datetime
    effective_to: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FiscalPendingItem(BaseModel):
    product_id: uuid.UUID
    product_name: str
    code: Optional[str] = None
    barcodes: List[str] = []
    has_profile: bool
    pending_reasons: List[str] = []


class FiscalPendingReportResponse(BaseModel):
    total_products: int
    pending_count: int
    ok_count: int
    items: List[FiscalPendingItem]
