from abc import ABC, abstractmethod
from typing import Optional
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.nfse_document import NfseDocument
from app.schemas.nfse import NfseEmissionResult


class BaseNfseAdapter(ABC):
    """
    Interface abstrata para Provedores de NFS-e (Strategy Pattern).
    Cada município ou padrão de fisco municipal deve ter seu adapter dedicado.
    """
    @abstractmethod
    def emit_nfse(
        self,
        db: Session,
        company: Company,
        doc: NfseDocument,
        cert_bytes: bytes,
        cert_password: str,
    ) -> NfseEmissionResult:
        """Emite a NFS-e (ou transmite a DPS) no provedor do município."""
        pass

    @abstractmethod
    def cancel_nfse(
        self,
        db: Session,
        company: Company,
        doc: NfseDocument,
        justification: str,
        cert_bytes: bytes,
        cert_password: str,
    ) -> NfseEmissionResult:
        """Cancela a NFS-e emitida."""
        pass
