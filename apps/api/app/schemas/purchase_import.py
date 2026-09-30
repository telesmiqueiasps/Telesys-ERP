import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class NfeSupplierPreviewDTO(BaseModel):
    cnpj: str
    name: str
    trade_name: Optional[str] = None
    ie: Optional[str] = None
    address: Optional[Dict[str, Any]] = None


class NfeItemPreviewDTO(BaseModel):
    item_number: int
    vendor_product_code: str
    description: str
    ncm: str
    cest: Optional[str] = None
    cfop: str
    uCom: str
    qCom: float
    vUnCom: float
    vProd: float
    vDesc: float = 0.0
    taxes: Dict[str, Any] = Field(default_factory=dict)
    
    suggested_local_product_id: Optional[uuid.UUID] = None
    suggested_local_product_name: Optional[str] = None
    suggested_conversion_factor: float = 1.0


class NfeInstallmentPreviewDTO(BaseModel):
    nDup: str
    dVenc: str
    vDup: float


class NfeImportPreviewResponse(BaseModel):
    access_key: str
    nfe_number: int
    nfe_series: int
    issue_date: str
    supplier: NfeSupplierPreviewDTO
    recipient_cnpj: str
    is_valid_recipient: bool
    is_duplicate_key: bool
    validation_errors: List[str] = Field(default_factory=list)
    totals: Dict[str, float] = Field(default_factory=dict)
    items: List[NfeItemPreviewDTO] = Field(default_factory=list)
    installments: List[NfeInstallmentPreviewDTO] = Field(default_factory=list)
    raw_xml: str


class ItemMappingConfirmationInput(BaseModel):
    item_number: int
    vendor_product_code: str
    local_product_id: uuid.UUID
    conversion_factor: float = Field(1.0, gt=0, description="Fator de conversão (ex: Caixa de 12 -> 12.0)")
    unit_cost_override: Optional[float] = Field(None, description="Custo unitário sobrescrito opcional")


class PurchaseConfirmInput(BaseModel):
    company_id: uuid.UUID
    access_key: str
    raw_xml: str
    supplier_cnpj: str
    supplier_name: str
    supplier_ie: Optional[str] = None
    items_mapping: List[ItemMappingConfirmationInput]
    notes: Optional[str] = None
    generate_accounts_payable: bool = Field(True, description="Lançar automaticamente os títulos no Contas a Pagar")
