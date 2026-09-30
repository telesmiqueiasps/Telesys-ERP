from sqlalchemy.orm import Session
from app.models.company import Company
from app.models.nfse_document import NfseDocument
from app.schemas.nfse import NfseEmissionResult
from app.services.nfse_adapters.base_adapter import BaseNfseAdapter


class PaulistanaNfseAdapter(BaseNfseAdapter):
    """
    Adapter para o Padrão Específico de São Paulo Capital / WebService Paulistana.
    Mantido em arquivo separado para integridade de arquitetura por município/provedor.
    """
    def emit_nfse(
        self,
        db: Session,
        company: Company,
        doc: NfseDocument,
        cert_bytes: bytes,
        cert_password: str,
    ) -> NfseEmissionResult:
        raise NotImplementedError("Transmissão WebService Paulistana (São Paulo Capital) pendente de integração local.")

    def cancel_nfse(
        self,
        db: Session,
        company: Company,
        doc: NfseDocument,
        justification: str,
        cert_bytes: bytes,
        cert_password: str,
    ) -> NfseEmissionResult:
        raise NotImplementedError("Cancelamento Paulistana pendente de integração.")
