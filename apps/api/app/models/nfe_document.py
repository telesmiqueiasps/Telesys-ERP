import uuid
import enum
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Boolean, Integer, Text, ForeignKey, DateTime, Numeric, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class NfeStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SIGNED = "SIGNED"
    TRANSMITTED = "TRANSMITTED"
    AUTHORIZED = "AUTHORIZED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class NfeDocument(Base):
    __tablename__ = "nfe_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    fiscal_operation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fiscal_operations.id"), nullable=True, index=True
    )
    sale_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sales.id"), nullable=True, index=True
    )
    purchase_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchases.id"), nullable=True, index=True
    )

    # Identificação SEFAZ
    access_key: Mapped[str] = mapped_column(String(44), nullable=False, unique=True, index=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # nNF
    series: Mapped[int] = mapped_column(Integer, nullable=False, default=1)   # serie
    model: Mapped[str] = mapped_column(String(2), nullable=False, default="55")  # 55
    nature_of_operation: Mapped[str] = mapped_column(String(60), nullable=False) # natOp
    
    operation_type_nfe: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # tpNF (0=Entrada, 1=Saída)
    purpose: Mapped[int] = mapped_column(Integer, nullable=False, default=1)             # finNFe (1=Normal, 2=Complementar, 3=Ajuste, 4=Devolução/Retorno)
    issue_type: Mapped[int] = mapped_column(Integer, nullable=False, default=1)   # tpEmis (1=Normal, 9=Contingência)
    environment: Mapped[int] = mapped_column(Integer, nullable=False, default=2)  # tpAmb (1=Produção, 2=Homologação)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=NfeStatus.DRAFT.value, index=True)

    # Dados do Emitente (Snapshot)
    issuer_cnpj: Mapped[str] = mapped_column(String(14), nullable=False)
    issuer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    issuer_trade_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    issuer_ie: Mapped[Optional[str]] = mapped_column(String(14), nullable=True)
    issuer_crt: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    issuer_uf: Mapped[str] = mapped_column(String(2), nullable=False)
    issuer_address: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Dados do Destinatário (Snapshot)
    recipient_cnpj_cpf: Mapped[str] = mapped_column(String(14), nullable=False)
    recipient_name: Mapped[str] = mapped_column(String(100), nullable=False)
    recipient_ie: Mapped[Optional[str]] = mapped_column(String(14), nullable=True)
    recipient_email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    recipient_uf: Mapped[str] = mapped_column(String(2), nullable=False)
    recipient_is_final_consumer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    recipient_is_tax_contributor: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recipient_address: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Totais da Nota Fiscal
    vProd: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    vFrete: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    vSeguro: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    vDesc: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    vOutro: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    
    vBC: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    vICMS: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    vFCP: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    vBCST: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    vST: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    vIPI: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    vPIS: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    vCOFINS: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    vNF: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)  # Valor Total da NF-e

    # Documentos Referenciados (ex: Devoluções)
    referenced_nfe_key: Mapped[Optional[str]] = mapped_column(String(44), nullable=True, index=True)
    additional_information: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Protocolo de Autorização SEFAZ
    protocol_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, index=True)  # nProt
    digest_value: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)     # digVal
    sefaz_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)   # cStat (100=Autorizado)
    sefaz_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)   # xMotivo
    authorized_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Conteúdo dos XMLs SEFAZ
    raw_xml: Mapped[Optional[str]] = mapped_column(Text, nullable=True)      # XML Rascunho (sem assinatura)
    signed_xml: Mapped[Optional[str]] = mapped_column(Text, nullable=True)   # XML Assinado A1 (<NFe>)
    proc_xml: Mapped[Optional[str]] = mapped_column(Text, nullable=True)     # XML Processado Final (<nfeProc>)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    items: Mapped[List["NfeItem"]] = relationship(
        "NfeItem",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="NfeItem.item_number.asc()"
    )


class NfeItem(Base):
    __tablename__ = "nfe_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nfe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nfe_documents.id"), nullable=False, index=True
    )
    item_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # nItem (1..N)
    
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=True
    )
    product_code: Mapped[str] = mapped_column(String(60), nullable=False) # cProd
    gtin: Mapped[str] = mapped_column(String(14), nullable=False, default="SEM GTIN") # cEAN
    description: Mapped[str] = mapped_column(String(120), nullable=False) # xProd
    ncm: Mapped[str] = mapped_column(String(8), nullable=False) # NCM
    cest: Mapped[Optional[str]] = mapped_column(String(7), nullable=True) # CEST
    cfop: Mapped[str] = mapped_column(String(4), nullable=False) # CFOP
    uCom: Mapped[str] = mapped_column(String(6), nullable=False, default="UN") # uCom
    qCom: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=1.0) # qCom
    vUnCom: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False) # vUnCom
    vProd: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False) # vProd
    
    uTrib: Mapped[str] = mapped_column(String(6), nullable=False, default="UN") # uTrib
    qTrib: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=1.0) # qTrib
    vUnTrib: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False) # vUnTrib

    vFrete: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    vSeguro: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    vDesc: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    vOutro: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)

    # Imutabilidade do cálculo fiscal apurado pelo TaxEngine
    tax_snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    document: Mapped["NfeDocument"] = relationship("NfeDocument", back_populates="items")
