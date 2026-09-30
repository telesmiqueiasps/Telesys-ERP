import uuid
from datetime import datetime, date, timezone
from typing import List, Optional
from sqlalchemy import String, Boolean, Integer, Text, ForeignKey, Date, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class FiscalOperation(Base):
    __tablename__ = "fiscal_operations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )

    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    operation_type: Mapped[str] = mapped_column(String(10), nullable=False, default="OUT")  # IN ou OUT
    purpose: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # 1=Normal, 2=Complementar, 3=Ajuste, 4=Devolução/Retorno
    
    affect_inventory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    affect_financial: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    # Modelos de documentos permitidos separados por vírgula (ex: "55,65")
    allowed_doc_models: Mapped[str] = mapped_column(String(50), nullable=False, default="55,65")
    
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relacionamento com as regras de cenário
    rules: Mapped[List["FiscalScenarioRule"]] = relationship(
        "FiscalScenarioRule",
        back_populates="fiscal_operation",
        cascade="all, delete-orphan",
        order_by="FiscalScenarioRule.priority.asc()"
    )


class FiscalScenarioRule(Base):
    __tablename__ = "fiscal_scenario_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    fiscal_operation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fiscal_operations.id"), nullable=False, index=True
    )

    description: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # Filtros de Cenário
    uf_origin: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)  # ex: "SP" ou None/null para qualquer
    uf_destination: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)  # ex: "RJ" ou None/null para qualquer
    is_same_uf: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)  # True=Mesma UF, False=UFs Diferentes, None=Qualquer
    
    is_final_consumer: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)  # True, False ou None=Qualquer
    is_tax_contributor: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)  # True (indIEDest=1), False (indIEDest=9 ou 2), None=Qualquer

    # Determinação Fiscal Resultante
    cfop: Mapped[str] = mapped_column(String(4), nullable=False)  # ex: "5102", "6102", "5405"
    cst_csosn_override: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    icms_aliquot_override: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    fcp_aliquot_override: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)

    # Vigência / Versão
    effective_from: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # Null = sem término de vigência
    
    # Prioridade de Resolução (menor número = maior precedência)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    fiscal_operation: Mapped["FiscalOperation"] = relationship(
        "FiscalOperation", back_populates="rules"
    )
