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
from app.schemas.nfe import NfeDocumentCreate, NfeItemCreate
from app.services.nfe_xml_builder import generate_access_key, calculate_mod11_dv, NfeXmlBuilder
from app.services.nfe_signer import NfeSigner
from app.services.nfe import create_nfe_draft, sign_nfe_document, attach_authorization_protocol
from app.services.company_fiscal import upload_and_save_certificate


class TestNfeModel55(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.Session()
        self.tenant_id = uuid.uuid4()
        
        # Criar empresa no banco em memória
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

        # Semear operações fiscais padrões para a empresa
        from app.services.fiscal_operation import get_company_fiscal_operations
        get_company_fiscal_operations(self.db, self.tenant_id, self.company.id)

    def tearDown(self):
        self.db.close()

    def test_access_key_mod11_generation(self):
        # Validação do algoritmo Módulo 11 da Chave SEFAZ
        dt = datetime(2026, 9, 27, 12, 0, 0, tzinfo=timezone.utc)
        key = generate_access_key(
            uf="SP",
            issue_date=dt,
            cnpj="12345678000199",
            model=55,
            series=1,
            number=1,
            cNF=12345678
        )
        self.assertEqual(len(key), 44)
        self.assertTrue(key.isdigit())
        self.assertEqual(key[:2], "35")  # cUF SP
        self.assertEqual(key[2:6], "2609") # AAMM

        # Validar cálculo do DV isolado
        key_43 = key[:43]
        expected_dv = calculate_mod11_dv(key_43)
        self.assertEqual(int(key[43]), expected_dv)

    def test_xml_builder_structure(self):
        # Testar construção do XML v4.00
        doc = NfeDocument(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company.id,
            access_key="35260912345678000199550010000000011123456789",
            number=1,
            series=1,
            model="55",
            nature_of_operation="VENDA NO ESTADO",
            issue_type=1,
            environment=2,
            status=NfeStatus.DRAFT.value,
            issuer_cnpj="12345678000199",
            issuer_name="EMPRESA MODELO LTDA",
            issuer_crt=1,
            issuer_uf="SP",
            recipient_cnpj_cpf="98765432000188",
            recipient_name="CLIENTE TESTE LTDA",
            recipient_uf="SP",
            recipient_is_final_consumer=True,
            recipient_is_tax_contributor=False,
            vProd=100.0,
            vNF=100.0,
            created_at=datetime.now(timezone.utc),
        )

        item = NfeItem(
            id=uuid.uuid4(),
            nfe_id=doc.id,
            item_number=1,
            product_code="PRD001",
            gtin="SEM GTIN",
            description="PRODUTO TESTE",
            ncm="84713012",
            cfop="5102",
            uCom="UN",
            qCom=1.0,
            vUnCom=100.0,
            vProd=100.0,
            uTrib="UN",
            qTrib=1.0,
            vUnTrib=100.0,
            tax_snapshot_json={
                "origem": "0",
                "icms": {"cst_csosn": "102", "vBC_ICMS": 0.0, "vICMS": 0.0},
                "pis": {"cst_pis": "07"},
                "cofins": {"cst_cofins": "07"},
            },
        )
        doc.items.append(item)

        raw_xml = NfeXmlBuilder.build_nfe_xml(doc)
        self.assertIn('<NFe xmlns="http://www.portalfiscal.inf.br/nfe">', raw_xml)
        self.assertIn('<infNFe Id="NFe35260912345678000199550010000000011123456789"', raw_xml)
        self.assertIn('<xProd>PRODUTO TESTE</xProd>', raw_xml)
        self.assertIn('<ICMSSN102>', raw_xml)
        self.assertIn('<vNF>100.00</vNF>', raw_xml)

    def test_digital_signature_a1_and_proc(self):
        # Generate synthetic RSA key & cert A1
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

        # Criar rascunho de NFe
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
                    vUnCom=150.0,
                    vProd=150.0,
                )
            ]
        )

        draft_doc = create_nfe_draft(self.db, self.tenant_id, payload)
        self.assertEqual(draft_doc.status, NfeStatus.DRAFT.value)
        self.assertIsNotNone(draft_doc.raw_xml)

        # Assinar digitalmente com o Certificado A1
        signed_doc = sign_nfe_document(self.db, self.tenant_id, draft_doc.id)
        self.assertEqual(signed_doc.status, NfeStatus.SIGNED.value)
        self.assertIn('<Signature xmlns="http://www.w3.org/2000/09/xmldsig#">', signed_doc.signed_xml)
        self.assertIn('<SignatureValue>', signed_doc.signed_xml)

        # Anexar protocolo SEFAZ (nfeProc)
        auth_doc = attach_authorization_protocol(
            self.db, self.tenant_id, signed_doc.id, protocol_number="135260009998877"
        )
        self.assertEqual(auth_doc.status, NfeStatus.AUTHORIZED.value)
        self.assertEqual(auth_doc.protocol_number, "135260009998877")
        self.assertIn('<nfeProc versao="4.00"', auth_doc.proc_xml)
        self.assertIn('<protNFe versao="4.00"', auth_doc.proc_xml)


if __name__ == "__main__":
    unittest.main()
