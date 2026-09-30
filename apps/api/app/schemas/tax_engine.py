import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# --- Input DTOs ---

class ProductTaxProfileInput(BaseModel):
    ncm: str = Field(..., max_length=8, example="84713012")
    cest: Optional[str] = Field(None, max_length=7, example="2103000")
    origem: str = Field("0", max_length=1, example="0")  # 0=Nacional
    cst_csosn: str = Field(..., max_length=4, example="102")
    cfop_padrao: Optional[str] = Field(None, max_length=4, example="5102")
    
    # Alíquotas Padrão do Produto
    icms_aliquot: Optional[float] = Field(None, ge=0, le=100)
    icms_st_aliquot: Optional[float] = Field(None, ge=0, le=100)
    mva_st: Optional[float] = Field(None, ge=0, le=1000)
    fcp_aliquot: Optional[float] = Field(None, ge=0, le=100)
    
    cst_ipi: Optional[str] = Field("99", max_length=2)
    ipi_aliquot: Optional[float] = Field(None, ge=0, le=100)
    
    cst_pis: Optional[str] = Field("07", max_length=2)
    pis_aliquot: Optional[float] = Field(None, ge=0, le=100)
    
    cst_cofins: Optional[str] = Field("07", max_length=2)
    cofins_aliquot: Optional[float] = Field(None, ge=0, le=100)

    # Reforma Tributária RTC (IBS e CBS)
    cst_ibs: Optional[str] = Field("01", max_length=3, description="CST do IBS")
    cst_cbs: Optional[str] = Field("01", max_length=3, description="CST da CBS")
    cClass: Optional[str] = Field(None, max_length=10, description="Código de Classificação Tributária IBS/CBS")
    ibs_aliquot: Optional[float] = Field(None, ge=0, le=100)
    ibs_state_aliquot: Optional[float] = Field(None, ge=0, le=100)
    ibs_mun_aliquot: Optional[float] = Field(None, ge=0, le=100)
    cbs_aliquot: Optional[float] = Field(None, ge=0, le=100)
    pRed_IBS: Optional[float] = Field(0.0, ge=0, le=100, description="Percentual de Redução da Base IBS")
    pRed_CBS: Optional[float] = Field(0.0, ge=0, le=100, description="Percentual de Redução da Base CBS")
    cBenef_IBS: Optional[str] = Field(None, max_length=20, description="Código do Benefício/Incentivo IBS")
    cBenef_CBS: Optional[str] = Field(None, max_length=20, description="Código do Benefício/Incentivo CBS")
    vCred_IBS: Optional[float] = Field(0.0, ge=0, description="Crédito Presumido/Apurado IBS")
    vCred_CBS: Optional[float] = Field(0.0, ge=0, description="Crédito Presumido/Apurado CBS")
    vDesc_IBS: Optional[float] = Field(0.0, ge=0, description="Desconto/Dedução de Benefício IBS")
    vDesc_CBS: Optional[float] = Field(0.0, ge=0, description="Desconto/Dedução de Benefício CBS")
    rtc_version: Optional[str] = Field("RTC_2026.1", description="Versão da Legislação RTC")


class RecipientInput(BaseModel):
    uf: str = Field(..., min_length=2, max_length=2, example="SP")
    is_final_consumer: bool = Field(True, description="Indica se é Consumidor Final")
    is_tax_contributor: bool = Field(False, description="Indica se é Contribuinte ICMS")
    ie: Optional[str] = Field(None, description="Inscrição Estadual")


class OperationResolvedInput(BaseModel):
    operation_code: str = Field(..., example="VENDA_ESTADO")
    operation_name: str = Field(..., example="Venda de Mercadoria no Estado")
    operation_type: str = Field("OUT", example="OUT")
    purpose: int = Field(1, description="1=Normal, 2=Complementar, 3=Ajuste, 4=Devolução")
    cfop: str = Field(..., min_length=4, max_length=4, example="5102")
    cst_csosn_override: Optional[str] = Field(None, max_length=4)
    icms_aliquot_override: Optional[float] = Field(None, ge=0, le=100)
    fcp_aliquot_override: Optional[float] = Field(None, ge=0, le=100)


class ItemFinancialContextInput(BaseModel):
    vProd: float = Field(..., gt=0, example=100.0, description="Valor total bruto do produto")
    qCom: float = Field(1.0, gt=0, example=1.0)
    vUnCom: float = Field(..., gt=0, example=100.0)
    vFrete: float = Field(0.0, ge=0, example=0.0)
    vSeguro: float = Field(0.0, ge=0, example=0.0)
    vOutro: float = Field(0.0, ge=0, example=0.0)
    vDesc: float = Field(0.0, ge=0, example=0.0)


class TaxCalculationInput(BaseModel):
    company_crt: int = Field(..., description="1=Simples Nacional, 2=Simples Nacional Excesso, 3=Regime Normal")
    company_uf: str = Field(..., min_length=2, max_length=2, example="SP")
    company_pCredSN: Optional[float] = Field(0.0, ge=0, le=100, description="Alíquota de crédito de ICMS do Simples Nacional (se CRT 1)")
    
    product: ProductTaxProfileInput
    operation: OperationResolvedInput
    recipient: RecipientInput
    context: ItemFinancialContextInput


# --- TaxSnapshot Imutável DTO Output ---

class TaxICMSSnapshot(BaseModel):
    cst_csosn: str
    modBC: int = 0  # 0=Margem Valor Agregado, 3=Valor da Operação
    vBC_ICMS: float = 0.0
    pICMS: float = 0.0
    vICMS: float = 0.0
    pCredSN: float = 0.0
    vCredICMSSN: float = 0.0


class TaxFCPSnapshot(BaseModel):
    vBC_FCP: float = 0.0
    pFCP: float = 0.0
    vFCP: float = 0.0


class TaxSTSnapshot(BaseModel):
    vBC_ICMSST: float = 0.0
    pMVAST: float = 0.0
    pICMSST: float = 0.0
    vICMSST: float = 0.0


class TaxDIFALSnapshot(BaseModel):
    vBC_DIFAL: float = 0.0
    pICMS_UF_Dest: float = 0.0
    pICMS_Inter: float = 0.0
    pICMS_Inter_Part: float = 100.0  # 100% para a UF de destino (pós-2019)
    vDIFAL_UF_Dest: float = 0.0
    vDIFAL_UF_Remet: float = 0.0


class TaxIPISnapshot(BaseModel):
    cst_ipi: str = "99"
    vBC_IPI: float = 0.0
    pIPI: float = 0.0
    vIPI: float = 0.0


class TaxPISSnapshot(BaseModel):
    cst_pis: str = "07"
    vBC_PIS: float = 0.0
    pPIS: float = 0.0
    vPIS: float = 0.0


class TaxCOFINSSnapshot(BaseModel):
    cst_cofins: str = "07"
    vBC_COFINS: float = 0.0
    pCOFINS: float = 0.0
    vCOFINS: float = 0.0


class TaxIBSSnapshot(BaseModel):
    """Grupo IBS (Imposto sobre Bens e Serviços) - Reforma Tributária Versionado"""
    version: str = Field("RTC_2026.1", description="Versão das regras de apuração do IBS")
    cst_ibs: str = Field("01", description="CST do IBS")
    cClass: Optional[str] = Field(None, description="Código de Classificação Tributária")
    cBenef_IBS: Optional[str] = Field(None, description="Código do Benefício/Incentivo Fiscal IBS")
    
    vBC_IBS: float = Field(0.0, ge=0, description="Base de Cálculo Bruta do IBS")
    pRed_IBS: float = Field(0.0, ge=0, le=100, description="Percentual de Redução da Base IBS")
    vRed_IBS: float = Field(0.0, ge=0, description="Valor da Redução da Base IBS")
    vBC_IBS_Efetiva: float = Field(0.0, ge=0, description="Base de Cálculo Efetiva do IBS")
    
    pIBS: float = Field(0.0, ge=0, le=100, description="Alíquota Total do IBS")
    pIBS_State: float = Field(0.0, ge=0, le=100, description="Alíquota do IBS Estadual")
    pIBS_Mun: float = Field(0.0, ge=0, le=100, description="Alíquota do IBS Municipal")
    
    vIBS_Bruto: float = Field(0.0, ge=0, description="Valor do IBS Bruto")
    vIBS_State: float = Field(0.0, ge=0, description="Valor do IBS Estadual")
    vIBS_Mun: float = Field(0.0, ge=0, description="Valor do IBS Municipal")
    vCred_IBS: float = Field(0.0, ge=0, description="Crédito de IBS")
    vDesc_IBS: float = Field(0.0, ge=0, description="Desconto/Dedução de Benefício IBS")
    vIBS: float = Field(0.0, ge=0, description="Valor do IBS Líquido Apurado")


class TaxCBSSnapshot(BaseModel):
    """Grupo CBS (Contribuição sobre Bens e Serviços) - Reforma Tributária Versionado"""
    version: str = Field("RTC_2026.1", description="Versão das regras de apuração da CBS")
    cst_cbs: str = Field("01", description="CST da CBS")
    cClass: Optional[str] = Field(None, description="Código de Classificação Tributária")
    cBenef_CBS: Optional[str] = Field(None, description="Código do Benefício/Incentivo Fiscal CBS")
    
    vBC_CBS: float = Field(0.0, ge=0, description="Base de Cálculo Bruta da CBS")
    pRed_CBS: float = Field(0.0, ge=0, le=100, description="Percentual de Redução da Base CBS")
    vRed_CBS: float = Field(0.0, ge=0, description="Valor da Redução da Base CBS")
    vBC_CBS_Efetiva: float = Field(0.0, ge=0, description="Base de Cálculo Efetiva da CBS")
    
    pCBS: float = Field(0.0, ge=0, le=100, description="Alíquota Total da CBS")
    vCBS_Bruto: float = Field(0.0, ge=0, description="Valor da CBS Bruta")
    vCred_CBS: float = Field(0.0, ge=0, description="Crédito de CBS")
    vDesc_CBS: float = Field(0.0, ge=0, description="Desconto/Dedução de Benefício CBS")
    vCBS: float = Field(0.0, ge=0, description="Valor da CBS Líquida Apurada")


class TaxRTCSnapshot(BaseModel):
    """Estrutura Consolidada e Versionada da Reforma Tributária (IBS e CBS)"""
    version: str = Field("RTC_2026.1", description="Versão do Modelo RTC")
    
    ibs: TaxIBSSnapshot = Field(default_factory=TaxIBSSnapshot)
    cbs: TaxCBSSnapshot = Field(default_factory=TaxCBSSnapshot)

    # Campos diretos de retrocompatibilidade
    vBC_IBS: float = 0.0
    pIBS: float = 0.0
    vIBS: float = 0.0
    vBC_CBS: float = 0.0
    pCBS: float = 0.0
    vCBS: float = 0.0


class TaxSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)  # Imutável

    calculation_id: str
    origem: str
    cfop: str
    
    vProd: float
    vFrete: float
    vSeguro: float
    vOutro: float
    vDesc: float
    vBC_Base: float  # (vProd + vFrete + vSeguro + vOutro - vDesc)
    
    icms: TaxICMSSnapshot
    fcp: TaxFCPSnapshot
    st: TaxSTSnapshot
    difal: TaxDIFALSnapshot
    ipi: TaxIPISnapshot
    pis: TaxPISSnapshot
    cofins: TaxCOFINSSnapshot
    rtc: TaxRTCSnapshot
    
    vTotTribAprox: float = 0.0  # Tributos aproximados (IBPT)
    vItemTotal: float  # vProd + vFrete + vSeguro + vOutro - vDesc + vICMSST + vIPI + vFCP
    
    audit_trail: List[str] = Field(default_factory=list, description="Trilha explicativa imutável dos cálculos realizados")
    warnings: List[str] = Field(default_factory=list, description="Alertas ou observações fiscais")
