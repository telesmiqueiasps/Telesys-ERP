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
from app.models.product import Product, ProductCategory, ProductUnit
from app.models.product_fiscal import ProductFiscalProfile
from app.models.fiscal_operation import FiscalOperation
from app.models.nfe_document import NfeDocument, NfeStatus
from app.models.stock import StockMovement
from app.models.audit import AuditLog
from app.schemas.special_operation import SpecialOperationCreateRequest, SpecialItemInput
from app.services.fiscal_operation import seed_default_fiscal_operations
from app.services.special_operation_service import create_special_operation_nfe
from app.core.crypto import encrypt_data


def generate_synthetic_pfx_and_password():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "EMPRESA TESTE LTDA:11222333000181"),
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


class TestSpecialFiscalOperations(unittest.TestCase):
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
            name="EMPRESA OPERACOES ESPECIAIS LTDA",
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

        # Semear Operações Fiscais Padrões (incluindo Devolução, Remessa, Transferência, Bonificação)
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
            subject_cn="EMPRESA TESTE LTDA:11222333000181",
            subject_cnpj="11222333000181",
            issuer="AC VALID SSL v5",
            serial_number="1234567890",
            valid_from=datetime.now(timezone.utc) - timedelta(days=1),
            valid_until=datetime.now(timezone.utc) + timedelta(days=365),
            is_active=True,
        )
        self.db.add(self.cert)

        # Unidade e Produto no Estoque
        self.unit = ProductUnit(id=uuid.uuid4(), name="Unidade", code="UN")
        self.db.add(self.unit)

        self.product = Product(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            unit_id=self.unit.id,
            code="PROD-MAQ-01",
            name="Equipamento de Medição de Alta Precisão",
            price=1500.00,
            cost=800.00,
            stock_qty=10.0,
            ncm="90318099",
        )
        self.db.add(self.product)

        self.profile = ProductFiscalProfile(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            product_id=self.product.id,
            ncm="90318099",
            origin=0,
            cst_csosn="102",
        )
        self.db.add(self.profile)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def test_devolucao_venda_referenced_key_validation(self):
        """Valida devolução exigindo Chave Referenciada de 44 dígitos e gerando tag <NFref><refNFe>."""
        original_ref_key = "35260999888777000199550010000005001123456789"
        payload = SpecialOperationCreateRequest(
            company_id=self.company_id,
            operation_code="DEVOLUCAO_VENDA",
            recipient_cnpj_cpf="99888777000199",
            recipient_name="CLIENTE COMPRADOR LTDA",
            recipient_uf="SP",
            referenced_nfe_key=original_ref_key,
            items=[
                SpecialItemInput(product_id=self.product.id, quantity=2.0, unit_price=1500.00)
            ],
        )

        doc = create_special_operation_nfe(
            db=self.db,
            tenant_id=self.tenant_id,
            payload=payload,
            user_id=self.user_id,
        )

        self.assertIsNotNone(doc)
        self.assertEqual(doc.purpose, 4) # finNFe 4 = Devolução
        self.assertEqual(doc.operation_type_nfe, 0) # tpNF 0 = Entrada (Devolução de Venda)
        self.assertEqual(doc.referenced_nfe_key, original_ref_key)

        # XML deve conter a tag <NFref><refNFe>
        self.assertIn("<NFref>", doc.raw_xml)
        self.assertIn(f"<refNFe>{original_ref_key}</refNFe>", doc.raw_xml)
        self.assertIn("<finNFe>4</finNFe>", doc.raw_xml)
        self.assertIn("<tpNF>0</tpNF>", doc.raw_xml)

        # Estoque deve ser incrementado (Entrada por devolução: 10 + 2 = 12)
        self.db.refresh(self.product)
        self.assertEqual(float(self.product.stock_qty), 12.0)

    def test_devolucao_missing_referenced_key_rejection(self):
        """Valida a rejeição se a Chave Referenciada for omitida ou tiver menos de 44 dígitos."""
        payload_invalid = SpecialOperationCreateRequest(
            company_id=self.company_id,
            operation_code="DEVOLUCAO_COMPRA",
            recipient_cnpj_cpf="99888777000199",
            recipient_name="FORNECEDOR LTDA",
            recipient_uf="SP",
            referenced_nfe_key="12345", # Chave curta inválida
            items=[
                SpecialItemInput(product_id=self.product.id, quantity=1.0, unit_price=800.00)
            ],
        )

        with self.assertRaises(ValueError) as ctx:
            create_special_operation_nfe(self.db, self.tenant_id, payload_invalid, self.user_id)

        self.assertIn("Deve possuir exatamente 44 dígitos numéricos", str(ctx.exception))

    def test_remessa_conserto_inventory_only(self):
        """Valida Remessa para Conserto movimentando estoque (Saída: 10 - 1 = 9) com finNFe 1 e sem gerar duplicata."""
        payload = SpecialOperationCreateRequest(
            company_id=self.company_id,
            operation_code="REMESSA_CONSERTO",
            recipient_cnpj_cpf="99888777000199",
            recipient_name="OFICINA E REPAROS SP LTDA",
            recipient_uf="SP",
            items=[
                SpecialItemInput(product_id=self.product.id, quantity=1.0, unit_price=1500.00)
            ],
        )

        doc = create_special_operation_nfe(
            db=self.db,
            tenant_id=self.tenant_id,
            payload=payload,
            user_id=self.user_id,
        )

        self.assertEqual(doc.purpose, 1) # finNFe 1 = Normal
        self.assertEqual(doc.operation_type_nfe, 1) # tpNF 1 = Saída
        self.assertIn("<finNFe>1</finNFe>", doc.raw_xml)
        self.assertIn("<tpNF>1</tpNF>", doc.raw_xml)

        # Estoque reduzido para 9.0
        self.db.refresh(self.product)
        self.assertEqual(float(self.product.stock_qty), 9.0)

        mov = self.db.scalar(select(StockMovement).where(StockMovement.product_id == self.product.id))
        self.assertIn("REMESSA_CONSERTO", mov.reference_doc)
        self.assertIn("Remessa para Conserto", mov.notes)

    def test_bonificacao_inventory_deduction(self):
        """Valida Bonificação/Brinde/Doação reduzindo estoque sem impactar o financeiro."""
        payload = SpecialOperationCreateRequest(
            company_id=self.company_id,
            operation_code="BONIFICACAO",
            recipient_cnpj_cpf="99888777000199",
            recipient_name="CLIENTE BONIFICADO SA",
            recipient_uf="RJ",
            items=[
                SpecialItemInput(product_id=self.product.id, quantity=3.0, unit_price=1500.00)
            ],
        )

        doc = create_special_operation_nfe(
            db=self.db,
            tenant_id=self.tenant_id,
            payload=payload,
            user_id=self.user_id,
        )

        self.assertIsNotNone(doc)
        self.assertEqual(doc.recipient_uf, "RJ")

        # Estoque reduzido de 10 para 7
        self.db.refresh(self.product)
        self.assertEqual(float(self.product.stock_qty), 7.0)

        # Registro de Auditoria
        audit = self.db.scalar(select(AuditLog).where(AuditLog.entity_id == doc.id))
        self.assertIsNotNone(audit)
        self.assertEqual(audit.action, "SPECIAL_OPERATION_NFE_CREATED")


if __name__ == "__main__":
    unittest.main()
