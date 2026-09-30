import uuid
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class FiscalReportFilterRequest(BaseModel):
    company_id: uuid.UUID
    report_type: str = Field(
        ...,
        description=(
            "Tipo do Relatório: EMITTED, RECEIVED, CANCELLED, INUTILIZED, REJECTED, "
            "CONTINGENCY, EVENTS, BY_CFOP, BY_CST, TAX_SUMMARY, RETURNS, PENDENCIES"
        ),
    )
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    model: Optional[str] = Field(None, description="Modelo: '55', '65' ou None para todos")
    cfop: Optional[str] = Field(None, description="Filtrar por código CFOP específico")
    cst_csosn: Optional[str] = Field(None, description="Filtrar por CST/CSOSN")
    recipient_cnpj_cpf: Optional[str] = Field(None, description="Filtrar por CPF/CNPJ do destinatário")
    issuer_cnpj: Optional[str] = Field(None, description="Filtrar por CNPJ do emitente")
    purpose: Optional[int] = Field(None, description="Finalidade: 1=Normal, 2=Complementar, 3=Ajuste, 4=Devolução")
    export_format: Optional[str] = Field("json", description="'json' ou 'csv'")


class FiscalReportRowItem(BaseModel):
    id: str
    date: str
    document_number: str
    series: str
    model: str
    access_key: Optional[str] = None
    operation_type: str
    purpose: str
    status: str
    entity_name: str
    entity_cnpj_cpf: str
    cfop: Optional[str] = None
    cst_csosn: Optional[str] = None
    vProd: float = 0.0
    vBC: float = 0.0
    vICMS: float = 0.0
    vFCP: float = 0.0
    vST: float = 0.0
    vIPI: float = 0.0
    vPIS: float = 0.0
    vCOFINS: float = 0.0
    vIBS: float = 0.0
    vCBS: float = 0.0
    vNF: float = 0.0
    notes_or_reason: Optional[str] = None


class FiscalReportGroupItem(BaseModel):
    key_code: str  # Ex: CFOP '5102' ou CST '00'
    description: str
    count_docs: int
    count_items: int
    vProd: float = 0.0
    vBC: float = 0.0
    vICMS: float = 0.0
    vFCP: float = 0.0
    vST: float = 0.0
    vIPI: float = 0.0
    vPIS: float = 0.0
    vCOFINS: float = 0.0
    vIBS: float = 0.0
    vCBS: float = 0.0
    vNF: float = 0.0


class TaxConsolidatedTotals(BaseModel):
    total_documents: int = 0
    total_vProd: float = 0.0
    total_vBC_ICMS: float = 0.0
    total_vICMS: float = 0.0
    total_vFCP: float = 0.0
    total_vBC_ST: float = 0.0
    total_vST: float = 0.0
    total_vIPI: float = 0.0
    total_vPIS: float = 0.0
    total_vCOFINS: float = 0.0
    total_vBC_IBS: float = 0.0
    total_vIBS: float = 0.0
    total_vBC_CBS: float = 0.0
    total_vCBS: float = 0.0
    total_vNF: float = 0.0


class FiscalReportSummaryResponse(BaseModel):
    report_type: str
    company_id: uuid.UUID
    generated_at: str
    filter_applied: Dict[str, Any]
    totals: TaxConsolidatedTotals
    rows: List[FiscalReportRowItem] = Field(default_factory=list)
    grouped_rows: List[FiscalReportGroupItem] = Field(default_factory=list)
    csv_content: Optional[str] = None
