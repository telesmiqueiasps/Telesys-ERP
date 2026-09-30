import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Integer, Boolean, UUID, ForeignKey, Numeric, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.company import Company
    from app.models.product import Product


class ProductFiscalProfile(Base, TimestampMixin):
    """
    Perfil Fiscal por Produto e Empresa.
    Parametrização completa para NF-e/NFC-e e Reforma Tributária (RTC IBS/CBS).
    Possui controle de vigência e histórico.
    """
    __tablename__ = "product_fiscal_profiles"

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
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Classificação Fiscal Basilar
    ncm: Mapped[str | None] = mapped_column(String(8), nullable=True, index=True)
    cest: Mapped[str | None] = mapped_column(String(7), nullable=True)
    origin: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 0-Nacional, etc.

    # GTINs e Unidades Tributáveis
    gtin_commercial: Mapped[str | None] = mapped_column(String(14), nullable=True)
    gtin_taxable: Mapped[str | None] = mapped_column(String(14), nullable=True)
    unit_commercial: Mapped[str | None] = mapped_column(String(10), nullable=True, default="UN")
    unit_taxable: Mapped[str | None] = mapped_column(String(10), nullable=True, default="UN")
    conversion_factor: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=1.0000)

    # Regras e Alíquotas do Sistema Legado (ICMS, IPI, PIS, COFINS)
    cst_csosn: Mapped[str | None] = mapped_column(String(4), nullable=True, default="102")
    cfop_default_inside: Mapped[str] = mapped_column(String(4), nullable=False, default="5102")
    cfop_default_outside: Mapped[str] = mapped_column(String(4), nullable=False, default="6102")
    icms_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0.00)
    icms_st_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0.00)
    fcp_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0.00)

    ipi_cst: Mapped[str | None] = mapped_column(String(3), nullable=True, default="99")
    ipi_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0.00)

    pis_cst: Mapped[str | None] = mapped_column(String(2), nullable=True, default="49")
    pis_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0.00)

    cofins_cst: Mapped[str | None] = mapped_column(String(2), nullable=True, default="49")
    cofins_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0.00)

    # Estrutura RTC (Reforma Tributária IBS / CBS Versionada)
    rtc_version: Mapped[str | None] = mapped_column(String(20), nullable=True, default="RTC_2026.1")
    tax_classification_code: Mapped[str | None] = mapped_column(String(10), nullable=True)  # cClass
    ibs_cst: Mapped[str | None] = mapped_column(String(3), nullable=True, default="01")
    ibs_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0.00)
    ibs_state_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0.00)
    ibs_mun_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0.00)
    ibs_reduction_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0.00)  # pRed_IBS
    ibs_benefit_code: Mapped[str | None] = mapped_column(String(10), nullable=True)  # cBenef_IBS

    cbs_cst: Mapped[str | None] = mapped_column(String(3), nullable=True, default="01")
    cbs_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0.00)
    cbs_reduction_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0.00)  # pRed_CBS
    cbs_benefit_code: Mapped[str | None] = mapped_column(String(10), nullable=True)  # cBenef_CBS

    # Controle de Vigência e Origem Legal
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.now)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    company: Mapped["Company"] = relationship("Company")
    product: Mapped["Product"] = relationship("Product", back_populates="fiscal_profile")


class ProductFiscalProfileHistory(Base):
    """
    Histórico imutável de alterações de perfil fiscal de produtos para auditoria e rastreabilidade.
    """
    __tablename__ = "product_fiscal_profile_histories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_fiscal_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    changed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.now)
