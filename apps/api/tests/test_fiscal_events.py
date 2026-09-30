import unittest
import uuid
from datetime import datetime, timezone, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.company import Company
from app.models.company_fiscal import FiscalCompanyConfig, FiscalCertificate
from app.models.nfe_document import NfeDocument, NfeItem, NfeStatus
from app.models.fiscal_event import FiscalEvent, FiscalInutilization, FiscalEventType
from app.schemas.nfe import NfeDocumentCreate, NfeItemCreate
from app.schemas.fiscal_event import (
    FiscalCancelRequest,
    FiscalCceRequest,
    FiscalInutilizationRequest,
)
from app.services.nfe import create_nfe_draft, sign_nfe_document, attach_authorization_protocol
from app.services.fiscal_event_service import cancel_nfe, cce_nfe, inutilizar_numeracao
from app.services.company_fiscal import upload_and_save_certificate, get_or_create_company_fiscal_config
from app.services.fiscal_operation import get_company_fiscal_operations


class TestFiscalEvents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.Session()
        self.tenant_id = uuid.uuid4()
        
        self.company = Company(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            name="EMPRESA MODELO LTDA",
            cnpj="12345678000199",
            state_registration="123456789",
            is_active=True,
        )
        self.db.add(self.company)
        self.db.commit()

        # Semear operações fiscais e certificados A1 para a empresa
        get_company_fiscal_operations(self.db, self.tenant_id, self.company.id)
        get_or_create_company_fiscal_config(self.db, self.tenant_id, self.company.id)

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "EMPRESA MODELO LTDA:12345678000199"),
        ])
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.now(timezone.utc) - timedelta(days=1)
        ).not_valid_after(
            datetime.now(timezone.utc) + timedelta(days=365)
        ).sign(key, hashes.SHA256())

        pfx_bytes = pkcs12.serialize_key_and_certificates(
            name=b"cert",
            key=key,
            cert=cert,
            cas=None,
            encryption_algorithm=serialization.BestAvailableEncryption(b"password123")
        )

        upload_and_save_certificate(
            self.db, self.tenant_id, self.company.id, "cert.pfx", pfx_bytes, "password123"
        )

    def tearDown(self):
        self.db.close()

    def _create_and_authorize_nfe(self) -> NfeDocument:
        payload = NfeDocumentCreate(
            company_id=self.company.id,
            fiscal_operation_code="VENDA_ESTADO",
            recipient_cnpj_cpf="98765432000188",
            recipient_name="CLIENTE TESTE",
            recipient_uf="SP",
            recipient_is_final_consumer=True,
            recipient_is_tax_contributor=False,
            items=[
                NfeItemCreate(
                    product_code="PRD001",
                    description="PRODUTO TESTE",
                    ncm="84713012",
                    qCom=1.0,
                    vUnCom=100.0,
                    vProd=100.0,
                )
            ]
        )
        draft = create_nfe_draft(self.db, self.tenant_id, payload)
        signed = sign_nfe_document(self.db, self.tenant_id, draft.id)
        auth = attach_authorization_protocol(self.db, self.tenant_id, signed.id)
        return auth

    def test_cancel_nfe_success(self):
        auth_nfe = self._create_and_authorize_nfe()
        self.assertEqual(auth_nfe.status, NfeStatus.AUTHORIZED.value)

        cancel_req = FiscalCancelRequest(
            nfe_id=auth_nfe.id,
            justification="Cancelamento solicitado pelo cliente antes da entrega dos produtos.",
        )

        event = cancel_nfe(self.db, self.tenant_id, cancel_req)
        self.assertEqual(event.event_type, FiscalEventType.CANCEL.value)
        self.assertEqual(event.seq_number, 1)
        self.assertIsNotNone(event.protocol_number)
        self.assertIn("<procEventoNFe", event.proc_xml)

        # Atualização do status da nota fiscal para CANCELLED
        self.db.refresh(auth_nfe)
        self.assertEqual(auth_nfe.status, NfeStatus.CANCELLED.value)

    def test_cancel_nfe_short_justification_rejection(self):
        auth_nfe = self._create_and_authorize_nfe()

        with self.assertRaises(Exception) as cm:
            FiscalCancelRequest(
                nfe_id=auth_nfe.id,
                justification="Curta",  # Menos de 15 caracteres!
            )
        self.assertTrue("15" in str(cm.exception) or "short" in str(cm.exception).lower())

    def test_cce_nfe_success_and_sequencing(self):
        auth_nfe = self._create_and_authorize_nfe()

        # Envio da 1ª Carta de Correção
        cce1_req = FiscalCceRequest(
            nfe_id=auth_nfe.id,
            correction_text="Correção da descrição do produto para Modelo Especial 2026.",
        )
        evt1 = cce_nfe(self.db, self.tenant_id, cce1_req)
        self.assertEqual(evt1.event_type, FiscalEventType.CCE.value)
        self.assertEqual(evt1.seq_number, 1)

        # Envio da 2ª Carta de Correção (sequencial 2)
        cce2_req = FiscalCceRequest(
            nfe_id=auth_nfe.id,
            correction_text="Correção da observação adicional de entrega no pedido.",
        )
        evt2 = cce_nfe(self.db, self.tenant_id, cce2_req)
        self.assertEqual(evt2.event_type, FiscalEventType.CCE.value)
        self.assertEqual(evt2.seq_number, 2)

        # Status da nota fiscal deve se manter AUTHORIZED
        self.db.refresh(auth_nfe)
        self.assertEqual(auth_nfe.status, NfeStatus.AUTHORIZED.value)

    def test_inutilization_success(self):
        inut_req = FiscalInutilizationRequest(
            company_id=self.company.id,
            model="55",
            series=1,
            year=2026,
            start_number=100,
            end_number=105,
            justification="Inutilização de numeração por falha técnica no emissor local.",
        )

        inut = inutilizar_numeracao(self.db, self.tenant_id, inut_req)
        self.assertEqual(inut.model, "55")
        self.assertEqual(inut.series, 1)
        self.assertEqual(inut.start_number, 100)
        self.assertEqual(inut.end_number, 105)
        self.assertIsNotNone(inut.protocol_number)
        self.assertIn("<inutNFe", inut.raw_xml)


if __name__ == "__main__":
    unittest.main()
