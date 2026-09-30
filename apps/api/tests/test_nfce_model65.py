import unittest
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.company import Company
from app.models.company_fiscal import FiscalCompanyConfig, FiscalSeries
from app.models.sale import Sale, SaleItem, SalePayment, SaleStatus
from app.models.nfe_document import NfeDocument, NfeItem, NfeStatus
from app.services.qr_code_generator import NfceQrCodeGenerator
from app.services.nfe_xml_builder import NfeXmlBuilder
from app.services.nfce_service import NfceService
from app.services.danfe_nfce_renderer import DanfeNfceRenderer


class TestNfceModel65(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.Session()
        self.tenant_id = uuid.uuid4()
        self.company_id = uuid.uuid4()

        self.company = Company(
            id=self.company_id,
            tenant_id=self.tenant_id,
            name="Loja PDV Modelo 65 LTDA",
            trade_name="Loja PDV",
            cnpj="11222333000181",
            state_registration="123456789",
        )
        self.db.add(self.company)

        self.fiscal_config = FiscalCompanyConfig(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            environment="HOMOLOGATION",
            tax_regime="SIMPLES_NACIONAL",
            crt=1,
            nfc_csc_id="000001",
            nfc_csc_secret_encrypted="123456",
        )
        self.db.add(self.fiscal_config)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_qr_code_generator_sha1(self):
        url = NfceQrCodeGenerator.generate_qr_code_str(
            access_key="35260911222333000181650010000001001123456781",
            environment=2,
            uf="SP",
            issue_date_hex="27092026",
            vNF=100.00,
            vICMS=18.00,
            digest_value_hex="4142434445464748495051525354555657585960",
            csc_id="000001",
            csc_secret="123456",
        )

        self.assertIn("https://www.homologacao.nfce.fazenda.sp.gov.br/qrcode", url)
        self.assertIn("?p=35260911222333000181650010000001001123456781|2|2||27092026|100.00|18.00|4142434445464748495051525354555657585960|000001|", url)

    def test_xml_builder_model65_tags(self):
        nfe_doc = NfeDocument(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            number=1,
            series=1,
            model="65",
            nature_of_operation="VENDA CONSUMIDOR",
            issuer_cnpj="11222333000181",
            issuer_name="Empresa Teste PDV",
            issuer_uf="SP",
            access_key="35260911222333000181650010000001001123456781",
            recipient_cnpj_cpf="",
            recipient_name="CONSUMIDOR NAO IDENTIFICADO",
            recipient_uf="SP",
            recipient_is_final_consumer=True,
            vNF=50.00,
            items=[
                NfeItem(
                    item_number=1,
                    product_code="PROD01",
                    description="Lanche Especial",
                    cfop="5102",
                    ncm="21069090",
                    qCom=1.0,
                    vUnCom=50.00,
                    vProd=50.00,
                    tax_snapshot_json={"icms": {"csosn": "102"}},
                )
            ],
        )
        setattr(nfe_doc, "qr_code_url", "http://nfce.sp.gov.br/qrcode?p=123")
        setattr(nfe_doc, "url_chave", "http://nfce.sp.gov.br/consulta")

        xml_str = NfeXmlBuilder.build_nfe_xml(nfe_doc)

        self.assertIn("<mod>65</mod>", xml_str)
        self.assertIn("<tpImp>4</tpImp>", xml_str)
        self.assertIn("<infNFeSupl>", xml_str)
        self.assertIn("<qrCode>http://nfce.sp.gov.br/qrcode?p=123</qrCode>", xml_str)

    def test_danfe_nfce_renderer_html(self):
        nfe_doc = NfeDocument(
            id=uuid.uuid4(),
            number=55,
            series=1,
            access_key="35260911222333000181650010000000551123456781",
            issuer_name="SUPERMERCADO TESTE",
            issuer_cnpj="11222333000181",
            issuer_uf="SP",
            vNF=120.00,
            vProd=120.00,
            issue_type=9,  # Contingência
            items=[
                NfeItem(
                    item_number=1,
                    product_code="BEB01",
                    description="Refrigerante 2L",
                    qCom=2.0,
                    uCom="UN",
                    vUnCom=10.00,
                    vProd=20.00,
                ),
                NfeItem(
                    item_number=2,
                    product_code="CAR01",
                    description="Carne Bovina 1kg",
                    qCom=1.0,
                    uCom="KG",
                    vUnCom=100.00,
                    vProd=100.00,
                ),
            ],
        )

        html = DanfeNfceRenderer.render_html(nfe_doc, qr_code_url="http://qr.code", url_chave="http://consulta.chave")

        self.assertIn("DANFE NFC-e - Nota Fiscal de Consumidor Eletrônica", html)
        self.assertIn("SUPERMERCADO TESTE", html)
        self.assertIn("EMITIDA EM CONTINGÊNCIA OFFLINE", html)
        self.assertIn("Refrigerante 2L", html)
        self.assertIn("Carne Bovina 1kg", html)
        self.assertIn("R$ 120.00", html)

    def test_nfce_service_issuance_and_contingency(self):
        user_id = uuid.uuid4()
        sale = Sale(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            user_id=user_id,
            code="VND-000099",
            status=SaleStatus.COMPLETED,
            subtotal=75.00,
            discount_amount=0.00,
            total_amount=75.00,
            items=[
                SaleItem(
                    item_number=1,
                    product_id=uuid.uuid4(),
                    product_name="Teclado USB Gamer",
                    unit_code="UN",
                    quantity=1.0,
                    unit_price=75.00,
                    discount_amount=0.00,
                    total_price=75.00,
                    ncm="84716052",
                )
            ],
            payments=[
                SalePayment(
                    payment_method="MONEY",
                    amount=80.00,
                    change_amount=5.00,
                )
            ],
        )
        self.db.add(sale)
        self.db.commit()

        # Executa a emissão da NFC-e via NfceService
        nfe_doc = NfceService.emit_nfce_for_sale(
            db=self.db,
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            sale=sale,
            issue_type=1,
            user_id=user_id,
        )

        self.assertIsNotNone(nfe_doc)
        self.assertEqual(nfe_doc.model, "65")
        self.assertEqual(nfe_doc.number, 1)
        self.assertEqual(nfe_doc.series, 1)
        self.assertIn(nfe_doc.status, (NfeStatus.AUTHORIZED.value, "AUTHORIZED_OFFLINE"))
        self.assertEqual(len(nfe_doc.items), 1)
        self.assertEqual(float(nfe_doc.vNF), 75.00)
