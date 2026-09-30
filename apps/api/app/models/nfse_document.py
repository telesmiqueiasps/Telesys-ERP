import uuid
import enum
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Text, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class NfseStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    DPS_GENERATED = "DPS_GENERATED"
    TRANSMITTED = "TRANSMITTED"
    ISSUED = "ISSUED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class NfseDocument(Base):
    """
    Nota Fiscal de Serviços Eletrônica (NFS-e).
    Representa serviços prestados sujeitos ao ISSQN (LC 116/03).
    Independente de NF-e (Modelo 55) e NFC-e (Modelo 65).
    """
    __tablename__ = "nfse_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Identificação da DPS (Declaração de Prestação de Serviços - Padrão Nacional / SEFIN)
    dps_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    dps_series: Mapped[str] = mapped_column(String(5), nullable=False, default="1")
    dps_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True) # ID na tag infDPS

    # Retorno da NFS-e Emitida pelo Fisco
    nfse_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, index=True)
    nfse_verification_code: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    access_key_national: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True, index=True) # Chave 50 dígitos NFS-e

    provider_type: Mapped[str] = mapped_column(String(30), nullable=False, default="NATIONAL") # NATIONAL, ABRASF_V2, PAULISTANA
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=NfseStatus.DRAFT.value, index=True)
    environment: Mapped[int] = mapped_column(Integer, nullable=False, default=2) # 1=Produção, 2=Homologação

    # Dados do Serviço
    service_code_lc116: Mapped[str] = mapped_column(String(10), nullable=False, index=True) # ex: '07.02', '17.06'
    national_tax_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True) # cTribNac
    service_description: Mapped[str] = mapped_column(Text, nullable=False)
    municipality_ibge: Mapped[str] = mapped_column(String(7), nullable=False) # cMun do local da prestação
    iss_taxation_type: Mapped[int] = mapped_column(Integer, nullable=False, default=1) # Exigibilidade do ISS

    # Snapshot Tomador (Customer)
    taker_document: Mapped[str] = mapped_column(String(14), nullable=False)
    taker_name: Mapped[str] = mapped_column(String(255), nullable=False)
    taker_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    taker_uf: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)

    # Valores Financeiros & ISSQN
    service_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False) # vServ
    deductions_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0) # vDed
    discount_unconditional: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    discount_conditional: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)

    iss_rate: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.0) # pAliq (ex: 0.0200 = 2.00%)
    iss_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0) # vISS
    iss_withheld: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    iss_retained_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)

    # Retenções Federais de Impostos de Serviços
    pis_retained: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    cofins_retained: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    csll_retained: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    ir_retained: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    inss_retained: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)

    net_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False) # Valor Líquido da NFS-e

    # Respostas e XMLs
    protocol_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sefaz_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sefaz_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    dps_raw_xml: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    signed_dps_xml: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    nfse_proc_xml: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    issued_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company")
