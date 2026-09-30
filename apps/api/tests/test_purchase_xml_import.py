import unittest
import uuid
from datetime import datetime, date
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.company import Company
from app.models.customer import Supplier
from app.models.product import Product, ProductCategory, ProductUnit, ProductBarcode
from app.models.stock import StockMovement
from app.models.purchase import Purchase, PurchaseItem, PurchaseStatus
from app.models.finance import AccountPayable
from app.models.audit import AuditLog
from app.services.nfe_xml_import_service import NfeXmlImportService
from app.schemas.purchase_import import PurchaseConfirmInput, ItemMappingConfirmationInput


SAMPLE_VENDOR_NFE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<nfeProc versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe">
  <NFe>
    <infNFe Id="NFe35260999888777000199550010000005001123456789" versao="4.00">
      <ide>
        <cUF>35</cUF>
        <cNF>12345678</cNF>
        <natOp>VENDA DE MERCADORIA</natOp>
        <mod>55</mod>
        <serie>1</serie>
        <nNF>500</nNF>
        <dhEmi>2026-09-27T10:00:00-03:00</dhEmi>
        <tpNF>1</tpNF>
        <idDest>1</idDest>
        <cMunFG>3550308</cMunFG>
        <tpImp>1</tpImp>
        <tpEmis>1</tpEmis>
        <cDV>9</cDV>
        <tpAmb>2</tpAmb>
        <finNFe>1</finNFe>
        <indFinal>0</indFinal>
        <indPres>1</indPres>
        <procEmi>0</procEmi>
        <verProc>1.0</verProc>
      </ide>
      <emit>
        <CNPJ>99888777000199</CNPJ>
        <xNome>DISTRIBUIDORA DE BEBIDAS E ALIMENTOS LTDA</xNome>
        <xFant>DISTRIBUIDORA BEBIDAS</xFant>
        <enderEmit>
          <xLgr>AV INDUSTRIAL</xLgr>
          <nro>1500</nro>
          <xBairro>DISTRITO INDUSTRIAL</xBairro>
          <cMun>3550308</cMun>
          <xMun>SAO PAULO</xMun>
          <UF>SP</UF>
          <CEP>01002000</CEP>
        </enderEmit>
        <IE>987654321</IE>
        <CRT>3</CRT>
      </emit>
      <dest>
        <CNPJ>11222333000181</CNPJ>
        <xNome>SUPERMERCADO TELESYS COMPRAS LTDA</xNome>
        <enderDest>
          <xLgr>RUA COMERCIAL</xLgr>
          <nro>200</nro>
          <xBairro>CENTRO</xBairro>
          <cMun>3550308</cMun>
          <xMun>SAO PAULO</xMun>
          <UF>SP</UF>
        </enderDest>
        <indIEDest>1</indIEDest>
        <IE>123456789</IE>
      </dest>
      <det nItem="1">
        <prod>
          <cProd>BEB-SUCO-01</cProd>
          <cEAN>7891234567890</cEAN>
          <xProd>Caixa de Suco de Laranja 1L (Caixa c/ 12 UN)</xProd>
          <NCM>20091200</NCM>
          <CFOP>5102</CFOP>
          <uCom>CX</uCom>
          <qCom>2.0000</qCom>
          <vUnCom>60.0000</vUnCom>
          <vProd>120.00</vProd>
          <cEANTrib>7891234567890</cEANTrib>
          <uTrib>CX</uTrib>
          <qTrib>2.0000</qTrib>
          <vUnTrib>60.0000</vUnTrib>
          <indTot>1</indTot>
        </prod>
        <imposto>
          <ICMS>
            <ICMS00>
              <orig>0</orig>
              <CST>00</CST>
              <modBC>3</modBC>
              <vBC>120.00</vBC>
              <pICMS>18.00</pICMS>
              <vICMS>21.60</vICMS>
            </ICMS00>
          </ICMS>
        </imposto>
      </det>
      <total>
        <ICMSTot>
          <vBC>120.00</vBC>
          <vICMS>21.60</vICMS>
          <vICMSDeson>0.00</vICMSDeson>
          <vFCP>0.00</vFCP>
          <vBCST>0.00</vBCST>
          <vST>0.00</vST>
          <vFCPST>0.00</vFCPST>
          <vFCPSTRet>0.00</vFCPSTRet>
          <vProd>120.00</vProd>
          <vFrete>0.00</vFrete>
          <vSeguro>0.00</vSeguro>
          <vDesc>0.00</vDesc>
          <vII>0.00</vII>
          <vIPI>0.00</vIPI>
          <vIPIDevol>0.00</vIPIDevol>
          <vPIS>0.00</vPIS>
          <vCOFINS>0.00</vCOFINS>
          <vOutro>0.00</vOutro>
          <vNF>120.00</vNF>
        </ICMSTot>
      </total>
      <transp>
        <modFrete>9</modFrete>
      </transp>
      <cobr>
        <fat>
          <nFat>500</nFat>
          <vOrig>120.00</vOrig>
          <vLiq>120.00</vLiq>
        </fat>
        <dup>
          <nDup>001</nDup>
          <dVenc>2026-10-27</dVenc>
          <vDup>120.00</vDup>
        </dup>
      </cobr>
    </infNFe>
  </NFe>
</nfeProc>"""


class TestPurchaseXmlImport(unittest.TestCase):
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

        # Company com CNPJ correspondente ao destinatário do XML (11222333000181)
        self.company = Company(
            id=self.company_id,
            tenant_id=self.tenant_id,
            name="SUPERMERCADO TELESYS COMPRAS LTDA",
            cnpj="11.222.333/0001-81",
            state_registration="123456789",
        )
        self.db.add(self.company)

        # Unidade e Categoria para Produto Local
        self.unit = ProductUnit(
            id=uuid.uuid4(),
            name="Unidade",
            code="UN",
        )
        self.db.add(self.unit)

        self.category = ProductCategory(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            name="Bebidas",
        )
        self.db.add(self.category)

        # Produto Local no estoque (Inicialmente: 5 unidades a R$ 4.00 cada)
        self.product = Product(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            category_id=self.category.id,
            unit_id=self.unit.id,
            code="PROD-SUCO-UN",
            name="Suco de Laranja 1L",
            price=8.00,
            cost=4.00,
            stock_qty=5.0,
            ncm="20091200",
        )
        self.db.add(self.product)

        self.product_barcode = ProductBarcode(
            id=uuid.uuid4(),
            product_id=self.product.id,
            barcode="7891234567890",
        )
        self.db.add(self.product_barcode)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def test_phase1_parse_and_preview_valid_nfe_xml(self):
        """FASE 1: Testa o parse e prévia do XML. Não deve alterar estoque nem gravar financeiro."""
        preview = NfeXmlImportService.parse_and_preview_xml(
            db=self.db,
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            xml_content=SAMPLE_VENDOR_NFE_XML,
        )

        self.assertEqual(preview.access_key, "35260999888777000199550010000005001123456789")
        self.assertEqual(preview.nfe_number, 500)
        self.assertEqual(preview.nfe_series, 1)
        self.assertTrue(preview.is_valid_recipient)
        self.assertFalse(preview.is_duplicate_key)
        self.assertEqual(len(preview.validation_errors), 0)

        # Fornecedor extraído
        self.assertEqual(preview.supplier.cnpj, "99888777000199")
        self.assertIn("DISTRIBUIDORA DE BEBIDAS", preview.supplier.name)

        # Itens e sugestão de de-para por GTIN (7891234567890)
        self.assertEqual(len(preview.items), 1)
        item0 = preview.items[0]
        self.assertEqual(item0.vendor_product_code, "BEB-SUCO-01")
        self.assertEqual(item0.uCom, "CX")
        self.assertEqual(item0.qCom, 2.0)
        self.assertEqual(item0.vUnCom, 60.0)
        self.assertEqual(item0.suggested_local_product_id, self.product.id)

        # Faturas
        self.assertEqual(len(preview.installments), 1)
        self.assertEqual(preview.installments[0].vDup, 120.00)

        # Garantia que FASE 1 NÃO alterou o banco (0 Compras e Estoque Intacto)
        count_purchases = self.db.query(Purchase).count()
        self.assertEqual(count_purchases, 0)
        self.assertEqual(self.product.stock_qty, 5.0)

    def test_duplicate_key_protection(self):
        """Testa o bloqueio contra importação de Chave de Acesso Duplicada."""
        # Pre-cadastra uma compra com a mesma chave de acesso
        existing_p = Purchase(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            user_id=self.user_id,
            code="COMP-EXISTING-01",
            status=PurchaseStatus.RECEIVED.value,
            access_key="35260999888777000199550010000005001123456789",
            import_status="CONFIRMED",
        )
        self.db.add(existing_p)
        self.db.commit()

        preview = NfeXmlImportService.parse_and_preview_xml(
            db=self.db,
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            xml_content=SAMPLE_VENDOR_NFE_XML,
        )

        self.assertTrue(preview.is_duplicate_key)
        self.assertTrue(any("já foi importada" in err for err in preview.validation_errors))

    def test_recipient_cnpj_divergence_protection(self):
        """Testa o bloqueio quando o CNPJ destinatário no XML não corresponde à empresa."""
        # Modifica o CNPJ da empresa local
        self.company.cnpj = "88.999.000/0001-11"
        self.db.add(self.company)
        self.db.commit()

        preview = NfeXmlImportService.parse_and_preview_xml(
            db=self.db,
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            xml_content=SAMPLE_VENDOR_NFE_XML,
        )

        self.assertFalse(preview.is_valid_recipient)
        self.assertTrue(any("não corresponde ao CNPJ da empresa" in err for err in preview.validation_errors))

    def test_phase2_confirm_and_execute_import_success(self):
        """FASE 2: Testa a efetivação explícita do operador após conferência do de-para.
        Deve atualizar estoque com conversão de unidades (2 Caixas x 12 UN = +24 UN),
        recalcular custo médio ponderado, lançar Contas a Pagar e gerar Auditoria.
        """
        confirm_input = PurchaseConfirmInput(
            company_id=self.company_id,
            access_key="35260999888777000199550010000005001123456789",
            raw_xml=SAMPLE_VENDOR_NFE_XML,
            supplier_cnpj="99888777000199",
            supplier_name="DISTRIBUIDORA DE BEBIDAS E ALIMENTOS LTDA",
            supplier_ie="987654321",
            items_mapping=[
                ItemMappingConfirmationInput(
                    item_number=1,
                    vendor_product_code="BEB-SUCO-01",
                    local_product_id=self.product.id,
                    conversion_factor=12.0,  # Cada caixa contém 12 unidades!
                )
            ],
            notes="Importado com sucesso via conferência de de-para",
            generate_accounts_payable=True,
        )

        purchase = NfeXmlImportService.confirm_and_execute_import(
            db=self.db,
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            user_id=self.user_id,
            confirm_input=confirm_input,
        )

        self.assertIsNotNone(purchase)
        self.assertEqual(purchase.access_key, "35260999888777000199550010000005001123456789")
        self.assertEqual(purchase.status, PurchaseStatus.RECEIVED.value)
        self.assertEqual(purchase.import_status, "CONFIRMED")
        self.assertEqual(len(purchase.items), 1)

        p_item = purchase.items[0]
        self.assertEqual(p_item.unit_conversion_factor, 12.0)
        self.assertEqual(p_item.quantity, 24.0)  # 2 CX x 12 UN = 24 UN
        self.assertEqual(p_item.unit_cost, 5.0)  # R$ 120.00 / 24 UN = R$ 5.00 cada

        # Validação do Estoque: 5 UN existentes (custo 4.00) + 24 UN novas (custo 5.00) = 29 UN
        # Custo médio ponderado = ((5 * 4.00) + (24 * 5.00)) / 29 = (20 + 120) / 29 = 140 / 29 = R$ 4.83
        self.db.refresh(self.product)
        self.assertEqual(float(self.product.stock_qty), 29.0)
        self.assertEqual(float(self.product.cost), 4.83)

        # Movimentação de Estoque criada
        mov = self.db.scalar(select(StockMovement).where(StockMovement.product_id == self.product.id))
        self.assertIsNotNone(mov)
        self.assertEqual(float(mov.quantity), 24.0)
        self.assertEqual(float(mov.unit_cost), 5.0)

        # Lançamento no Contas a Pagar
        ap = self.db.scalar(select(AccountPayable).where(AccountPayable.purchase_id == purchase.id))
        self.assertIsNotNone(ap)
        self.assertEqual(float(ap.amount), 120.00)
        self.assertEqual(ap.status, "PENDING")

        # Registro de Auditoria
        audit = self.db.scalar(select(AuditLog).where(AuditLog.entity_id == purchase.id))
        self.assertIsNotNone(audit)
        self.assertEqual(audit.action, "PURCHASE_NFE_IMPORTED")
