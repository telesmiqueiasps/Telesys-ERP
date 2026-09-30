import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, UUID, ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.company import Company


class FiscalCompanyConfig(Base, TimestampMixin):
    """
    Configuração Fiscal da Empresa/Filial.
    Parâmetros de ambiente, CRT/Regime Tributário, Inscrição Estadual/Municipal,
    Token CSC (NFC-e), NFS-e e Modo de Contingência.
    """
    __tablename__ = "fiscal_company_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # Parametrização Tributária e Identificação
    environment: Mapped[str] = mapped_column(String(20), nullable=False, default="HOMOLOGATION")  # HOMOLOGATION / PRODUCTION
    tax_regime: Mapped[str] = mapped_column(String(30), nullable=False, default="SIMPLES_NACIONAL")  # SIMPLES_NACIONAL / MEI / REGIME_NORMAL
    crt: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # 1-Simples, 2-Simples Excesso, 3-Regime Normal, 4-MEI
    state_tax_number: Mapped[str | None] = mapped_column(String(20), nullable=True)  # Inscrição Estadual (IE)
    municipal_tax_number: Mapped[str | None] = mapped_column(String(20), nullable=True)  # Inscrição Municipal (IM)
    ibge_city_code: Mapped[str | None] = mapped_column(String(7), nullable=True)  # Código IBGE do Município (ex: 3550308 - SP)

    # NFC-e Token CSC (Código de Segurança do Contribuinte para QR Code)
    nfc_csc_id: Mapped[str | None] = mapped_column(String(10), nullable=True)
    nfc_csc_secret_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Parâmetros de NFS-e (Nota de Serviços)
    nfse_provider: Mapped[str | None] = mapped_column(String(50), nullable=True, default="NACIONAL")  # NACIONAL / GINFES / BETHA / etc.
    nfse_environment: Mapped[str] = mapped_column(String(20), nullable=False, default="HOMOLOGATION")

    # Parâmetros de Modo de Contingência
    contingency_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="NONE")  # NONE / OFFLINE_NFC / EPEC
    contingency_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contingency_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    company: Mapped["Company"] = relationship("Company")


class FiscalSeries(Base, TimestampMixin):
    """
    Controle sequencial e isolado de séries de numeração fiscal por empresa e modelo de documento.
    """
    __tablename__ = "fiscal_series"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    doc_model: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # '55' (NF-e), '65' (NFC-e), 'NFS'
    series: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    current_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    environment: Mapped[str] = mapped_column(String(20), nullable=False, default="HOMOLOGATION")  # HOMOLOGATION / PRODUCTION
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    company: Mapped["Company"] = relationship("Company")


class FiscalCertificate(Base, TimestampMixin):
    """
    Certificado Digital A1 da empresa/filial armazenado com criptografia simétrica Fernet.
    """
    __tablename__ = "fiscal_certificates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    certificate_data_encrypted: Mapped[str] = mapped_column(Text, nullable=False)  # PKCS12 binary encrypted
    password_encrypted: Mapped[str] = mapped_column(Text, nullable=False)  # Password encrypted

    # Metadados seguros extraídos do X.509
    subject_cn: Mapped[str] = mapped_column(String(255), nullable=False)  # Razão Social / Nome do Titular
    subject_cnpj: Mapped[str | None] = mapped_column(String(18), nullable=True)  # CNPJ do titular
    issuer: Mapped[str] = mapped_column(String(255), nullable=False)  # AC Emissora
    serial_number: Mapped[str] = mapped_column(String(100), nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    company: Mapped["Company"] = relationship("Company")
