import uuid
from typing import List, Optional
from pydantic import BaseModel, Field


class SpecialItemInput(BaseModel):
    product_id: uuid.UUID
    quantity: float = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)


class SpecialOperationCreateRequest(BaseModel):
    company_id: uuid.UUID
    operation_code: str = Field(..., description="DEVOLUCAO_COMPRA, DEVOLUCAO_VENDA, REMESSA_CONSERTO, REMESSA_DEMONSTRACAO, TRANSFERENCIA, BONIFICACAO")
    recipient_cnpj_cpf: str = Field(..., description="CPF/CNPJ do destinatário")
    recipient_name: str = Field(..., description="Nome / Razão Social do destinatário")
    recipient_uf: str = Field(..., min_length=2, max_length=2)
    recipient_is_final_consumer: bool = True
    recipient_is_tax_contributor: bool = False

    referenced_nfe_key: Optional[str] = Field(None, description="Chave de Acesso da NF-e original (obrigatoria para Devolução - 44 dígitos)")
    notes: Optional[str] = None
    items: List[SpecialItemInput] = Field(..., min_length=1)


class ComplementaryAdjustmentCreateRequest(BaseModel):
    company_id: uuid.UUID
    purpose: int = Field(..., description="Finalidade da NF-e: 2 (Complementar) ou 3 (Ajuste)")
    referenced_nfe_key: str = Field(..., description="Chave de Acesso da NF-e original (obrigatoriamente 44 dígitos numéricos)")
    reason: str = Field(..., min_length=10, description="Motivo / Justificativa detalhada do complemento ou ajuste fiscal")

    recipient_cnpj_cpf: str = Field(..., description="CPF/CNPJ do destinatário")
    recipient_name: str = Field(..., description="Nome / Razão Social do destinatário")
    recipient_uf: str = Field(..., min_length=2, max_length=2)
    recipient_is_final_consumer: bool = True
    recipient_is_tax_contributor: bool = False

    operation_code: Optional[str] = Field(None, description="Código da Operação Fiscal. Se omisso, usa NFE_COMPLEMENTAR ou NFE_AJUSTE.")
    affect_inventory: bool = Field(False, description="Indica se afeta saldo físico de estoque")
    affect_financial: bool = Field(False, description="Indica se gera títulos financeiros")

    notes: Optional[str] = None
    items: List[SpecialItemInput] = Field(..., min_length=1)

