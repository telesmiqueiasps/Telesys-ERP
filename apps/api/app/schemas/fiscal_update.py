import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class FiscalRuleVersionInput(BaseModel):
    rule_code: str = Field(..., max_length=50, example="RULE_IBS_CBS_2026")
    rule_name: str = Field(..., max_length=150, example="Alíquotas e Reduções da Reforma Tributária")
    scope: str = Field("TAX_CALCULATION", description="SEFAZ_VALIDATION, TAX_CALCULATION ou SCHEMA_XSD")
    old_value_json: Optional[dict] = None
    new_value_json: dict = Field(..., example={"pIBS": 0.15, "pCBS": 0.90})
    is_breaking_change: bool = False
    requires_user_confirmation: bool = True


class FiscalSchemaVersionCreate(BaseModel):
    company_id: uuid.UUID
    doc_model: str = Field("55", description="55 (NFe), 65 (NFCe), NFS, RTC")
    schema_version: str = Field(..., max_length=20, example="v4.00")
    technical_note: str = Field(..., max_length=50, example="NT 2024.001 v1.20")
    title: str = Field(..., max_length=150, example="NT 2024.001 - Alterações de Schemas e Regras IBS/CBS")
    description: Optional[str] = None
    homologation_effective_date: datetime = Field(..., description="Data de vigência obrigatória em Homologação")
    production_effective_date: datetime = Field(..., description="Data de vigência obrigatória em Produção")
    requires_explicit_approval: bool = Field(True, description="REGRA: Não atualizar silenciosamente")
    rules: List[FiscalRuleVersionInput] = Field(default_factory=list)


class FiscalRuleApplyRequest(BaseModel):
    user_id: uuid.UUID = Field(..., description="ID do usuário responsável pela aprovação explícita")
    environment: str = Field("HOMOLOGATION", description="HOMOLOGATION ou PRODUCTION")
    notes: Optional[str] = Field(None, description="Observações ou justificativa do usuário")


class FiscalRuleRejectRequest(BaseModel):
    user_id: uuid.UUID = Field(..., description="ID do usuário que rejeitou a atualização")
    rejection_reason: str = Field(..., min_length=10, description="Motivo / Justificativa detalhada da rejeição")


class FiscalRuleVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rule_code: str
    rule_name: str
    scope: str
    old_value_json: Optional[dict] = None
    new_value_json: dict
    is_breaking_change: bool
    requires_user_confirmation: bool
    status: str
    created_at: datetime


class FiscalSchemaVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    company_id: uuid.UUID
    doc_model: str
    schema_version: str
    technical_note: str
    title: str
    description: Optional[str] = None
    homologation_effective_date: datetime
    production_effective_date: datetime
    status: str
    requires_explicit_approval: bool
    applied_at: Optional[datetime] = None
    applied_by_user_id: Optional[uuid.UUID] = None
    rejection_reason: Optional[str] = None
    rules_changes_json: dict = Field(default_factory=dict)
    rules: List[FiscalRuleVersionResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class FiscalUpdateAuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    schema_version_id: uuid.UUID
    action: str
    user_id: uuid.UUID
    details_json: dict
    created_at: datetime
