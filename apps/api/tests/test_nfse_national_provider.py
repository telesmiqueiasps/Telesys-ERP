import unittest
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12

from app.models.base import Base
from app.models.company import Company
from app.models.company_fiscal import FiscalCertificate
from app.models.nfse_document import NfseDocument, NfseStatus
from app.models.audit import AuditLog
from app.schemas.nfse import NfseCreateRequest, NfseCancelRequest
from app.services.nfse_adapters.national_adapter import NationalNfseXmlBuilder, NationalNfseAdapter
from app.services.nfse_adapters.abrasf_v2_adapter import AbrasfV2Adapter
from app.services.nfse_adapters.paulistana_adapter import PaulistanaNfseAdapter
from app.services.nfse_provider import NfseProviderFactory
from app.services.nfse_service import create_and_emit_nfse, cancel_nfse_document
from app.core.crypto import encrypt_data


def generate_synthetic_pfx_and_password():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "EMPRESA PRESTADORA LTDA:11222333000181"),
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

    password = "senha_cert_123"
    pfx_bytes = pkcs12.serialize_key_and_certificates(
        name=b"cert_a1",
        key=key,
        cert=cert,
        cas=None,
        encryption_algorithm=serialization.BestAvailableEncryption(password.encode("utf-8")),
    )
    return pfx_bytes, password


class TestNfseNationalProvider(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.Session()
        self.tenant_id = uuid.uuid4()
        self.company_id = uuid.uuid4()
        self.user_id = uuid.uuid4()

        # Empresa Prestadora
        self.company = Company(
            id=self.company_id,
            tenant_id=self.tenant_id,
            name="TELESYS SERVICOS DE TECNOLOGIA LTDA",
            cnpj="11.222.333/0001-81",
            state_registration="123456789",
        )
        self.db.add(self.company)

        # Certificado A1 Sintético
        pfx_bytes, pwd = generate_synthetic_pfx_and_password()
        self.cert = FiscalCertificate(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            filename="cert_a1.pfx",
            certificate_data_encrypted=encrypt_data(pfx_bytes),
            password_encrypted=encrypt_data(pwd),
            subject_cn="EMPRESA PRESTADORA LTDA:11222333000181",
            subject_cnpj="11222333000181",
            issuer="AC VALID SSL v5",
            serial_number="1234567890",
            valid_from=datetime.now(timezone.utc) - timedelta(days=1),
            valid_until=datetime.now(timezone.utc) + timedelta(days=365),
            is_active=True,
        )
        self.db.add(self.cert)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def test_nfse_dps_xml_builder_structure(self):
        """Valida a construção do XML da DPS Padrão Nacional (SEFIN / Convênio ATV 192/2023)."""
        doc = NfseDocument(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            dps_number=1,
            dps_series="1",
            dps_id="DPS1122233300018100001000000000000001",
            service_code_lc116="17.06",
            national_tax_code="170601",
            service_description="Desenvolvimento e licenciamento de softwares de ERP fiscal.",
            municipality_ibge="3550308",
            taker_document="99888777000199",
            taker_name="TOMADOR DE SERVICOS LTDA",
            service_amount=1000.00,
            deductions_amount=0.00,
            discount_unconditional=0.00,
            iss_rate=0.02, # 2%
            iss_amount=20.00,
            net_amount=1000.00,
            environment=2,
        )

        xml = NationalNfseXmlBuilder.build_dps_xml(self.company, doc)
        self.assertIn('<DPS xmlns="http://www.nfse.gov.br/schema/NFS-e_v1.00.xsd"', xml)
        self.assertIn('<infDPS Id="DPS1122233300018100001000000000000001"', xml)
        self.assertIn('<cTribNac>170601</cTribNac>', xml)
        self.assertIn('<cLocPrestacao>3550308</cLocPrestacao>', xml)
        self.assertIn('<vServ>1000.00</vServ>', xml)
        self.assertIn('<vISS>20.00</vISS>', xml)

    def test_nfse_provider_factory_resolution(self):
        """Valida a resolução dinâmica de adapters pelo NfseProviderFactory."""
        national_adapter = NfseProviderFactory.get_adapter("NATIONAL")
        self.assertIsInstance(national_adapter, NationalNfseAdapter)

        abrasf_adapter = NfseProviderFactory.get_adapter("ABRASF_V2")
        self.assertIsInstance(abrasf_adapter, AbrasfV2Adapter)

        paulistana_adapter = NfseProviderFactory.get_adapter("PAULISTANA")
        self.assertIsInstance(paulistana_adapter, PaulistanaNfseAdapter)

        # Default fallback para nacional
        default_adapter = NfseProviderFactory.get_adapter("UNKNOWN_CITY")
        self.assertIsInstance(default_adapter, NationalNfseAdapter)

    def test_national_nfse_emission_flow(self):
        """Valida a emissão completa de NFS-e via Padrão Nacional, com geração da Chave Nacional de 50 dígitos e XML procNFSe."""
        payload = NfseCreateRequest(
            company_id=self.company_id,
            service_code_lc116="17.06",
            national_tax_code="170601",
            service_description="Consultoria em arquitetura de TI e sistemas fiscais.",
            municipality_ibge="3550308",
            taker_document="99888777000199",
            taker_name="CLIENTE TOMADOR SA",
            service_amount=2500.00,
            iss_rate=2.5, # 2.5%
            iss_withheld=False,
            pis_retained=16.25,
            cofins_retained=75.00,
            provider_type="NATIONAL",
        )

        result = create_and_emit_nfse(
            db=self.db,
            tenant_id=self.tenant_id,
            payload=payload,
            user_id=self.user_id,
        )

        self.assertTrue(result.success)
        self.assertEqual(result.status, NfseStatus.ISSUED.value)
        self.assertIsNotNone(result.access_key_national)
        self.assertTrue(result.access_key_national.startswith("NFS"))
        self.assertEqual(len(result.access_key_national), 50)
        self.assertIsNotNone(result.nfse_number)
        self.assertIsNotNone(result.nfse_verification_code)
        self.assertEqual(result.sefaz_status_code, 100)

        # Verificar persistência no BD
        doc = self.db.scalar(select(NfseDocument).where(NfseDocument.id == result.nfse_id))
        self.assertIsNotNone(doc)
        self.assertEqual(doc.status, "ISSUED")
        self.assertIn("<Signature", doc.signed_dps_xml)
        self.assertIn("<nfseProc", doc.nfse_proc_xml)

        # Trilha de Auditoria
        audit = self.db.scalar(select(AuditLog).where(AuditLog.entity_id == result.nfse_id))
        self.assertIsNotNone(audit)
        self.assertEqual(audit.action, "NFSE_EMITTED")

    def test_nfse_cancellation_flow(self):
        """Valida o cancelamento da NFS-e com justificativa e alteração do status."""
        payload = NfseCreateRequest(
            company_id=self.company_id,
            service_code_lc116="07.02",
            service_description="Serviço de manutenção em infraestrutura.",
            municipality_ibge="3550308",
            taker_document="99888777000199",
            taker_name="TOMADOR EXTRATO SA",
            service_amount=500.00,
            iss_rate=2.0,
            provider_type="NATIONAL",
        )
        emission_res = create_and_emit_nfse(
            db=self.db,
            tenant_id=self.tenant_id,
            payload=payload,
            user_id=self.user_id,
        )

        cancel_payload = NfseCancelRequest(
            justification="Serviço de manutenção cancelado de comum acordo entre as partes contratantes."
        )

        cancel_res = cancel_nfse_document(
            db=self.db,
            tenant_id=self.tenant_id,
            nfse_id=emission_res.nfse_id,
            payload=cancel_payload,
            user_id=self.user_id,
        )

        self.assertTrue(cancel_res.success)
        self.assertEqual(cancel_res.status, NfseStatus.CANCELLED.value)
        self.assertEqual(cancel_res.sefaz_status_code, 101)

        doc = self.db.scalar(select(NfseDocument).where(NfseDocument.id == emission_res.nfse_id))
        self.assertEqual(doc.status, "CANCELLED")


if __name__ == "__main__":
    unittest.main()
