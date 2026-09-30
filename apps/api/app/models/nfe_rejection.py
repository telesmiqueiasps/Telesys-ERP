import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class NfeRejectionLog(Base):
    __tablename__ = "nfe_rejection_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    nfe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nfe_documents.id"), nullable=False, index=True
    )

    access_key: Mapped[str] = mapped_column(String(44), nullable=False, index=True)
    sefaz_code: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # cStat (ex: 204, 208, 215)
    official_message: Mapped[str] = mapped_column(String(255), nullable=False)   # xMotivo oficial SEFAZ
    
    # Lista de campos afetados no cadastro ou no XML (ex: ["emit.CNPJ", "det[1].ncm"])
    affected_fields: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Orientação de solução operacional (apenas se suportada oficialmente pela documentação)
    operational_solution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    raw_sefaz_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
