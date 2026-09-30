import uuid
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# --- FiscalScenarioRule Schemas ---

class FiscalScenarioRuleBase(BaseModel):
    description: str = Field(..., max_length=200, example="Venda de Mercadoria Interna no Estado")
    uf_origin: Optional[str] = Field(None, max_length=2, example="SP")
    uf_destination: Optional[str] = Field(None, max_length=2, example="SP")
    is_same_uf: Optional[bool] = Field(None, description="True se mesma UF, False se UF diferente, None para qualquer")
    is_final_consumer: Optional[bool] = Field(None, description="True se Consumidor Final, False se Revendedor, None para qualquer")
    is_tax_contributor: Optional[bool] = Field(None, description="True se Contribuinte ICMS, False se Não-Contribuinte, None para qualquer")
    
    cfop: str = Field(..., min_length=4, max_length=4, example="5102")
    cst_csosn_override: Optional[str] = Field(None, max_length=4, example="102")
    icms_aliquot_override: Optional[float] = Field(None, ge=0, le=100)
    fcp_aliquot_override: Optional[float] = Field(None, ge=0, le=100)
    
    effective_from: date = Field(default_factory=date.today)
    effective_to: Optional[date] = Field(None)
    priority: int = Field(10, ge=1, le=100)
    is_active: bool = True


class FiscalScenarioRuleCreate(FiscalScenarioRuleBase):
    pass


class FiscalScenarioRuleUpdate(BaseModel):
    description: Optional[str] = Field(None, max_length=200)
    uf_origin: Optional[str] = Field(None, max_length=2)
    uf_destination: Optional[str] = Field(None, max_length=2)
    is_same_uf: Optional[bool] = None
    is_final_consumer: Optional[bool] = None
    is_tax_contributor: Optional[bool] = None
    cfop: Optional[str] = Field(None, min_length=4, max_length=4)
    cst_csosn_override: Optional[str] = Field(None, max_length=4)
    icms_aliquot_override: Optional[float] = None
    fcp_aliquot_override: Optional[float] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    priority: Optional[int] = Field(None, ge=1, le=100)
    is_active: Optional[bool] = None


class FiscalScenarioRuleResponse(FiscalScenarioRuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    company_id: uuid.UUID
    fiscal_operation_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# --- FiscalOperation Schemas ---

class FiscalOperationBase(BaseModel):
    code: str = Field(..., max_length=50, example="VENDA_ESTADO")
    name: str = Field(..., max_length=150, example="Venda de Mercadoria no Estado")
    operation_type: str = Field("OUT", max_length=10, description="IN ou OUT")
    purpose: int = Field(1, description="1=Normal, 2=Complementar, 3=Ajuste, 4=Devolução/Retorno")
    affect_inventory: bool = True
    affect_financial: bool = True
    allowed_doc_models: str = Field("55,65", description="Modelos permitidos separados por vírgula (ex: 55,65)")
    description: Optional[str] = None
    is_active: bool = True


class FiscalOperationCreate(FiscalOperationBase):
    rules: Optional[List[FiscalScenarioRuleCreate]] = Field(default_factory=list)


class FiscalOperationUpdate(BaseModel):
    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=150)
    operation_type: Optional[str] = Field(None, max_length=10)
    purpose: Optional[int] = None
    affect_inventory: Optional[bool] = None
    affect_financial: Optional[bool] = None
    allowed_doc_models: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class FiscalOperationResponse(FiscalOperationBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    company_id: uuid.UUID
    rules: List[FiscalScenarioRuleResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# --- Scenario Matching Schemas ---

class FiscalScenarioMatchRequest(BaseModel):
    operation_code: Optional[str] = Field(None, description="Código da Operação Fiscal (ex: VENDA_ESTADO). Se omitido, busca por tipo (OUT/IN)")
    operation_type: str = Field("OUT", description="IN ou OUT")
    uf_origin: str = Field(..., min_length=2, max_length=2, example="SP")
    uf_destination: str = Field(..., min_length=2, max_length=2, example="SP")
    is_final_consumer: bool = Field(True, description="Indica se destinatário é consumidor final")
    is_tax_contributor: bool = Field(False, description="Indica se destinatário é contribuinte ICMS")
    doc_model: str = Field("55", description="Modelo de documento fiscal emitido (55, 65, 68)")
    operation_date: Optional[date] = Field(default_factory=date.today, description="Data da operação para filtro de vigência")


class FiscalScenarioMatchResult(BaseModel):
    matched: bool
    fiscal_operation_id: Optional[uuid.UUID] = None
    operation_name: Optional[str] = None
    purpose: Optional[int] = None
    affect_inventory: Optional[bool] = None
    affect_financial: Optional[bool] = None
    rule_id: Optional[uuid.UUID] = None
    rule_description: Optional[str] = None
    cfop: Optional[str] = None
    cst_csosn_override: Optional[str] = None
    icms_aliquot_override: Optional[float] = None
    fcp_aliquot_override: Optional[float] = None
    reason: str
