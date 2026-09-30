import uuid
import enum
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class FiscalEventType(str, enum.Enum):
    CANCEL = "110111"        # Cancelamento de NF-e / NFC-e
    CCE = "110110"           # Carta de Correção Eletrônica
    MANIFEST_SCIENCE = "210200" # Ciência da Operação
    MANIFEST_CONFIRM = "210210" # Confirmação da Operação
    INUTILIZATION = "INUT"    # Inutilização de Numeração


class FiscalEvent(Base):
    __tablename__ = "fiscal_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    nfe_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nfe_documents.id"), nullable=True, index=True
    )

    access_key: Mapped[str] = mapped_column(String(44), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # ex: '110111', '110110'
    event_name: Mapped[str] = mapped_column(String(100), nullable=False)            # ex: 'Cancelamento', 'CC-e'
    seq_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)      # nSeqEvento (1..20)
    
    justification_or_correction: Mapped[str] = mapped_column(Text, nullable=False) # xJust / xCorrecao

    # Retorno SEFAZ do Evento
    protocol_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, index=True) # nProt
    sefaz_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)             # cStat (135/136=Evento registrado)
    sefaz_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)             # xMotivo
    registered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Conteúdo dos XMLs do Evento
    raw_xml: Mapped[Optional[str]] = mapped_column(Text, nullable=True)      # XML evento rascunho
    signed_xml: Mapped[Optional[str]] = mapped_column(Text, nullable=True)   # XML evento assinado
    proc_xml: Mapped[Optional[str]] = mapped_column(Text, nullable=True)     # XML procEventoNFe

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class FiscalInutilization(Base):
    __tablename__ = "fiscal_inutilizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )

    model: Mapped[str] = mapped_column(String(2), nullable=False, default="55")  # '55' ou '65'
    series: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    year: Mapped[int] = mapped_column(Integer, nullable=False)                   # AAAA (ex: 2026)
    start_number: Mapped[int] = mapped_column(Integer, nullable=False)          # nNFIni
    end_number: Mapped[int] = mapped_column(Integer, nullable=False)            # nNFFin
    
    justification: Mapped[str] = mapped_column(Text, nullable=False)             # xJust (mín 15 caracteres)

    # Retorno SEFAZ
    protocol_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, index=True) # nProt
    sefaz_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)             # cStat (102=Inutilização de número homologado)
    sefaz_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)             # xMotivo
    registered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    raw_xml: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proc_xml: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
