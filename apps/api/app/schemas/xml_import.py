from typing import List, Optional
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field


class NfeSupplierXml(BaseModel):
    document: str
    name: str
    trade_name: Optional[str] = None
    state_registration: Optional[str] = None
    phone: Optional[str] = None
    address_street: Optional[str] = None
    address_number: Optional[str] = None
    address_neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None


class NfeItemXmlParsed(BaseModel):
    item_number: int
    cProd: str
    cEAN: Optional[str] = None
    xProd: str
    ncm: Optional[str] = None
    cest: Optional[str] = None
    uCom: str
    qCom: float
    vUnCom: float
    vProd: float
    matched_product_id: Optional[UUID] = None
    matched_product_name: Optional[str] = None


class NfeDupXmlParsed(BaseModel):
    nDup: str
    dVenc: str
    vDup: float


class NfeParseResponse(BaseModel):
    chNFe: str
    nNF: str
    serie: str
    dhEmi: Optional[str] = None
    supplier: NfeSupplierXml
    items: List[NfeItemXmlParsed]
    duplicatas: List[NfeDupXmlParsed]
    total_vProd: float
    total_vNF: float


class NfeConfirmItemInput(BaseModel):
    item_number: int
    cProd: str
    cEAN: Optional[str] = None
    name: str
    ncm: Optional[str] = None
    uCom: str
    quantity: float = Field(..., gt=0)
    unit_cost: float = Field(..., ge=0)
    action: str = Field(..., description="'CREATE_NEW' ou 'LINK_EXISTING'")
    linked_product_id: Optional[UUID] = None


class NfeConfirmImportInput(BaseModel):
    chNFe: str
    nNF: str
    supplier: NfeSupplierXml
    items: List[NfeConfirmItemInput]
    duplicatas: List[NfeDupXmlParsed] = []
    generate_payables: bool = True
