import uuid
import enum
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Boolean, Integer, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class FiscalUpdateStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    APPLIED = "APPLIED"
    REJECTED = "REJECTED"


class FiscalSchemaVersion(Base):
    __tablename__ = "fiscal_schema_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )

    doc_model: Mapped[str] = mapped_column(String(10), nullable=False, default="55") # '55', '65', 'NFS', 'RTC'
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False, index=True) # ex: 'v4.00', 'RTC_2026.1'
    technical_note: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # ex: 'NT 2024.001 v1.20'
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Datas Obrigatórias de Vigência
    homologation_effective_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    production_effective_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Controle Não-Silencioso de Atualização
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=FiscalUpdateStatus.PENDING_APPROVAL.value, index=True
    )
    requires_explicit_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    applied_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Payload das regras modificadas
    rules_changes_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    rules: Mapped[List["FiscalRuleVersion"]] = relationship(
        "FiscalRuleVersion", back_populates="schema_version_rel", cascade="all, delete-orphan"
    )


class FiscalRuleVersion(Base):
    __tablename__ = "fiscal_rule_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    schema_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fiscal_schema_versions.id"), nullable=False, index=True
    )

    rule_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # ex: 'RULE_IBS_2026'
    rule_name: Mapped[str] = mapped_column(String(150), nullable=False)
    scope: Mapped[str] = mapped_column(String(50), nullable=False, default="TAX_CALCULATION") # 'SEFAZ_VALIDATION', 'TAX_CALCULATION', 'SCHEMA_XSD'

    old_value_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    new_value_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    is_breaking_change: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_user_confirmation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=FiscalUpdateStatus.PENDING_APPROVAL.value
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    schema_version_rel: Mapped["FiscalSchemaVersion"] = relationship(
        "FiscalSchemaVersion", back_populates="rules"
    )


class FiscalUpdateAudit(Base):
    __tablename__ = "fiscal_update_audits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    schema_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fiscal_schema_versions.id"), nullable=False, index=True
    )

    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # 'REGISTERED', 'APPROVED', 'APPLIED', 'REJECTED'
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    details_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
