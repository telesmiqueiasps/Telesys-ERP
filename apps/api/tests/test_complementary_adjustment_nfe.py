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
from app.models.company_fiscal import FiscalCompanyConfig, FiscalCertificate
from app.models.product import Product, ProductUnit
from app.models.product_fiscal import ProductFiscalProfile
from app.models.fiscal_operation import FiscalOperation
from app.models.nfe_document import NfeDocument, NfeStatus
from app.models.audit import AuditLog
from app.schemas.special_operation import ComplementaryAdjustmentCreateRequest, SpecialItemInput
from app.services.fiscal_operation import seed_default_fiscal_operations
from app.services.special_operation_service import create_complementary_adjustment_nfe
from app.core.crypto import encrypt_data


def generate_synthetic_pfx_and_password():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "EMPRESA COMPLEMENTAR LTDA:11222333000181"),
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


class TestComplementaryAdjustmentNfe(unittest.TestCase):
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

        # Empresa Emissora
        self.company = Company(
            id=self.company_id,
            tenant_id=self.tenant_id,
            name="EMPRESA COMPLEMENTAR E AJUSTE LTDA",
            cnpj="11.222.333/0001-81",
            state_registration="123456789",
        )
        self.db.add(self.company)

        # Configuração Fiscal da Empresa
        self.fiscal_config = FiscalCompanyConfig(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            crt=1,
            tax_regime="SIMPLES_NACIONAL",
        )
        self.db.add(self.fiscal_config)

        # Semear Operações Fiscais Padrões (incluindo NFE_COMPLEMENTAR e NFE_AJUSTE)
        seed_default_fiscal_operations(self.db, self.tenant_id, self.company_id)

        # Certificado A1 Sintético
        pfx_bytes, pwd = generate_synthetic_pfx_and_password()
        self.cert = FiscalCertificate(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            filename="cert_a1.pfx",
            certificate_data_encrypted=encrypt_data(pfx_bytes),
            password_encrypted=encrypt_data(pwd),
            subject_cn="EMPRESA COMPLEMENTAR LTDA:11222333000181",
            subject_cnpj="11222333000181",
            issuer="AC VALID SSL v5",
            serial_number="1234567890",
            valid_from=datetime.now(timezone.utc) - timedelta(days=1),
            valid_until=datetime.now(timezone.utc) + timedelta(days=365),
            is_active=True,
        )
        self.db.add(self.cert)

        # Unidade e Produto
        self.unit = ProductUnit(id=uuid.uuid4(), name="Unidade", code="UN")
        self.db.add(self.unit)

        self.product = Product(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            unit_id=self.unit.id,
            code="PROD-AJUSTE-01",
            name="Produto para Ajuste / Complemento Fiscal",
            price=200.00,
            cost=100.00,
            stock_qty=50.0,
            ncm="20091200",
        )
        self.db.add(self.product)

        self.profile = ProductFiscalProfile(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            product_id=self.product.id,
            ncm="20091200",
            origin=0,
            cst_csosn="102",
        )
        self.db.add(self.profile)

        # NF-e Original no banco (para validar que NÃO é substituída)
        self.original_access_key = "35260911222333000181550010000001001987654321"
        self.original_doc = NfeDocument(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            access_key=self.original_access_key,
            number=100,
            series=1,
            model="55",
            nature_of_operation="Venda de Mercadoria",
            operation_type_nfe=1,
            purpose=1,
            issue_type=1,
            environment=2,
            status=NfeStatus.AUTHORIZED.value,
            issuer_cnpj=self.company.cnpj,
            issuer_name=self.company.name,
            issuer_uf="SP",
            recipient_cnpj_cpf="99888777000199",
            recipient_name="CLIENTE DESTINATARIO LTDA",
            recipient_uf="SP",
            vProd=1000.00,
            vNF=1000.00,
            protocol_number="135260000123456",
        )
        self.db.add(self.original_doc)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def test_nfe_complementar_success(self):
        """Valida emissão de NF-e Complementar (finNFe 2) referenciando chave original e adicionando motivo em <infCpl>."""
        reason = "Complemento de ICMS referente a erro no destaque de alíquota na NF-e original número 100"
        payload = ComplementaryAdjustmentCreateRequest(
            company_id=self.company_id,
            purpose=2,  # Complementar
            referenced_nfe_key=self.original_access_key,
            reason=reason,
            recipient_cnpj_cpf="99888777000199",
            recipient_name="CLIENTE DESTINATARIO LTDA",
            recipient_uf="SP",
            items=[
                SpecialItemInput(product_id=self.product.id, quantity=1.0, unit_price=50.00)
            ],
        )

        doc = create_complementary_adjustment_nfe(
            db=self.db,
            tenant_id=self.tenant_id,
            payload=payload,
            user_id=self.user_id,
        )

        self.assertIsNotNone(doc)
        self.assertEqual(doc.purpose, 2)  # finNFe 2
        self.assertEqual(doc.referenced_nfe_key, self.original_access_key)
        self.assertIn("NF-E COMPLEMENTAR REFERENTE A NF-E CHAVE", doc.additional_information)
        self.assertIn(reason, doc.additional_information)

        # XML deve conter <finNFe>2</finNFe>, <refNFe> e <infAdic><infCpl>
        self.assertIn("<finNFe>2</finNFe>", doc.raw_xml)
        self.assertIn(f"<refNFe>{self.original_access_key}</refNFe>", doc.raw_xml)
        self.assertIn("<infAdic>", doc.raw_xml)
        self.assertIn("<infCpl>", doc.raw_xml)
        self.assertIn(reason, doc.raw_xml)

    def test_nfe_ajuste_success(self):
        """Valida emissão de NF-e de Ajuste (finNFe 3) com chave referenciada e justificativa fiscal."""
        reason = "Ajuste escritural de estorno de crédito ICMS conforme Resolução SFA 45/2026"
        payload = ComplementaryAdjustmentCreateRequest(
            company_id=self.company_id,
            purpose=3,  # Ajuste
            referenced_nfe_key=self.original_access_key,
            reason=reason,
            recipient_cnpj_cpf="99888777000199",
            recipient_name="CLIENTE DESTINATARIO LTDA",
            recipient_uf="RJ",
            items=[
                SpecialItemInput(product_id=self.product.id, quantity=1.0, unit_price=100.00)
            ],
        )

        doc = create_complementary_adjustment_nfe(
            db=self.db,
            tenant_id=self.tenant_id,
            payload=payload,
            user_id=self.user_id,
        )

        self.assertIsNotNone(doc)
        self.assertEqual(doc.purpose, 3)  # finNFe 3
        self.assertIn("<finNFe>3</finNFe>", doc.raw_xml)
        self.assertIn(f"<refNFe>{self.original_access_key}</refNFe>", doc.raw_xml)
        self.assertIn(reason, doc.additional_information)

    def test_missing_or_invalid_referenced_key_rejection(self):
        """Rejeita quando a chave referenciada for omitida ou tiver tamanho diferente de 44 dígitos."""
        payload_short_key = ComplementaryAdjustmentCreateRequest(
            company_id=self.company_id,
            purpose=2,
            referenced_nfe_key="123456789",  # Inválida
            reason="Complemento de valor por diferença de preço unitário",
            recipient_cnpj_cpf="99888777000199",
            recipient_name="CLIENTE DESTINATARIO LTDA",
            recipient_uf="SP",
            items=[
                SpecialItemInput(product_id=self.product.id, quantity=1.0, unit_price=50.00)
            ],
        )

        with self.assertRaises(ValueError) as ctx:
            create_complementary_adjustment_nfe(self.db, self.tenant_id, payload_short_key, self.user_id)

        self.assertIn("Deve possuir exatamente 44 dígitos numéricos", str(ctx.exception))

    def test_blank_or_short_reason_rejection(self):
        """Rejeita se o motivo da emissão for vago ou tiver menos de 10 caracteres."""
        with self.assertRaises((ValueError, Exception)) as ctx:
            ComplementaryAdjustmentCreateRequest(
                company_id=self.company_id,
                purpose=2,
                referenced_nfe_key=self.original_access_key,
                reason="Ajuste",  # Curto demais (< 10 caracteres)
                recipient_cnpj_cpf="99888777000199",
                recipient_name="CLIENTE DESTINATARIO LTDA",
                recipient_uf="SP",
                items=[
                    SpecialItemInput(product_id=self.product.id, quantity=1.0, unit_price=50.00)
                ],
            )

        self.assertTrue("at least 10" in str(ctx.exception) or "mínimo 10" in str(ctx.exception))

    def test_invalid_purpose_rejection(self):
        """Rejeita se a finalidade não for 2 (Complementar) ou 3 (Ajuste)."""
        payload_invalid_purpose = ComplementaryAdjustmentCreateRequest(
            company_id=self.company_id,
            purpose=1,  # Normal (inválido para esta rota)
            referenced_nfe_key=self.original_access_key,
            reason="Tentativa de usar finalidade 1 em complemento",
            recipient_cnpj_cpf="99888777000199",
            recipient_name="CLIENTE DESTINATARIO LTDA",
            recipient_uf="SP",
            items=[
                SpecialItemInput(product_id=self.product.id, quantity=1.0, unit_price=50.00)
            ],
        )

        with self.assertRaises(ValueError) as ctx:
            create_complementary_adjustment_nfe(self.db, self.tenant_id, payload_invalid_purpose, self.user_id)

        self.assertIn("Deve ser 2 (Complementar) ou 3 (Ajuste)", str(ctx.exception))

    def test_original_nfe_not_replaced_or_altered(self):
        """Garante rigorosamente que a nota original no banco NÃO seja substituída nem modificada."""
        orig_status_before = self.original_doc.status
        orig_access_key_before = self.original_doc.access_key
        orig_number_before = self.original_doc.number

        payload = ComplementaryAdjustmentCreateRequest(
            company_id=self.company_id,
            purpose=2,
            referenced_nfe_key=self.original_access_key,
            reason="Complemento de imposto relativo a documento anterior",
            recipient_cnpj_cpf="99888777000199",
            recipient_name="CLIENTE DESTINATARIO LTDA",
            recipient_uf="SP",
            items=[
                SpecialItemInput(product_id=self.product.id, quantity=1.0, unit_price=30.00)
            ],
        )

        new_doc = create_complementary_adjustment_nfe(
            db=self.db,
            tenant_id=self.tenant_id,
            payload=payload,
            user_id=self.user_id,
        )

        # Recarrega nota original do banco
        self.db.refresh(self.original_doc)

        # Nota original deve continuar intocada
        self.assertEqual(self.original_doc.status, orig_status_before)
        self.assertEqual(self.original_doc.access_key, orig_access_key_before)
        self.assertEqual(self.original_doc.number, orig_number_before)

        # Nova nota criada possui ID e número próprios
        self.assertNotEqual(new_doc.id, self.original_doc.id)
        self.assertNotEqual(new_doc.access_key, self.original_doc.access_key)
        self.assertGreater(new_doc.number, self.original_doc.number)


if __name__ == "__main__":
    unittest.main()
