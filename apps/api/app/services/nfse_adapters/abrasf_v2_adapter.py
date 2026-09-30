from sqlalchemy.orm import Session
from app.models.company import Company
from app.models.nfse_document import NfseDocument
from app.schemas.nfse import NfseEmissionResult
from app.services.nfse_adapters.base_adapter import BaseNfseAdapter


class AbrasfV2Adapter(BaseNfseAdapter):
    """
    Adapter para Municípios no Padrão ABRASF v2.0x (ex: Betha, IPM, GISS, SigISS).
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
        raise NotImplementedError("Transmissão ABRASF v2.0x para este município está pendente de integração de WebService local.")

    def cancel_nfse(
        self,
        db: Session,
        company: Company,
        doc: NfseDocument,
        justification: str,
        cert_bytes: bytes,
        cert_password: str,
    ) -> NfseEmissionResult:
        raise NotImplementedError("Cancelamento ABRASF v2.0x pendente de integração.")
