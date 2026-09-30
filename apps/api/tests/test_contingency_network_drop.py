import unittest
import uuid
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.company import Company
from app.models.company_fiscal import FiscalCompanyConfig
from app.models.sale import Sale, SaleItem, SalePayment, SaleStatus
from app.models.nfe_document import NfeDocument, NfeStatus
from app.services.nfce_service import NfceService
from app.services.fiscal_reconciler import FiscalReconciler
from app.services.sefaz_adapter import SefazResponse


class TestContingencyNetworkDrop(unittest.TestCase):
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
            name="Supermercado Resiliente LTDA",
            cnpj="11222333000181",
            state_registration="123456789",
        )
        self.db.add(self.company)

        self.fiscal_config = FiscalCompanyConfig(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            environment="HOMOLOGATION",
            crt=1,
        )
        self.db.add(self.fiscal_config)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    @patch("app.services.nfce_service.SefazServiceAdapter.send_request")
    def test_network_drop_before_transmission_fallback_to_contingency(self, mock_sefaz_send):
        """Simula a QUEDA DE INTERNET durante a emissão no checkout do PDV.
        Deve efetuar o fallback automático e transparente para Contingência Offline (tpEmis 9).
        """
        # Simula erro de conexão de rede / Socket Timeout
        mock_sefaz_send.side_effect = ConnectionError("Queda de sinal de internet / SEFAZ indisponível")

        user_id = uuid.uuid4()
        sale = Sale(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            user_id=user_id,
            code="VND-OFF-001",
            status=SaleStatus.COMPLETED,
            subtotal=50.00,
            discount_amount=0.00,
            total_amount=50.00,
            items=[
                SaleItem(
                    item_number=1,
                    product_id=uuid.uuid4(),
                    product_name="Arroz 5kg",
                    unit_code="UN",
                    quantity=1.0,
                    unit_price=50.00,
                    discount_amount=0.00,
                    total_price=50.00,
                    ncm="10063021",
                )
            ],
            payments=[
                SalePayment(
                    payment_method="MONEY",
                    amount=50.00,
                    change_amount=0.00,
                )
            ],
        )
        self.db.add(sale)
        self.db.commit()

        # Finaliza a venda - deve capturar a queda de rede e autorizar offline
        nfe_doc = NfceService.emit_nfce_for_sale(
            db=self.db,
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            sale=sale,
            issue_type=1,
            user_id=user_id,
        )

        self.assertIsNotNone(nfe_doc)
        self.assertEqual(nfe_doc.status, "AUTHORIZED_OFFLINE")
        self.assertEqual(nfe_doc.issue_type, 9)
        self.assertTrue(nfe_doc.protocol_number.startswith("CONTINGENCIA-"))
        self.assertIn("contingência offline por indisponibilidade", nfe_doc.sefaz_reason)
        self.assertIsNotNone(nfe_doc.signed_xml)

    @patch("app.services.fiscal_reconciler.SefazServiceAdapter.send_request")
    def test_network_drop_during_transmission_reconciliation(self, mock_sefaz_send):
        """Simula a QUEDA DE INTERNET OCORRIDA DURANTE A TRANSMISSÃO.
        A SEFAZ autorizou a nota, mas a resposta não chegou ao ERP devido ao corte de conexão.
        Quando a fila posterior tentar reenviar, a SEFAZ retornará Rejeição 204 (Duplicidade).
        O FiscalReconciler deve consultar o protocolo na SEFAZ e promover a nota a AUTORIZADA com sucesso.
        """
        doc = NfeDocument(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            number=99,
            series=1,
            model="65",
            nature_of_operation="VENDA CONSUMIDOR",
            access_key="35260911222333000181650010000000999123456781",
            issuer_cnpj="11222333000181",
            issuer_name="Supermercado Resiliente LTDA",
            issuer_uf="SP",
            recipient_cnpj_cpf="",
            recipient_name="CONSUMIDOR FINAL",
            recipient_uf="SP",
            status="AUTHORIZED_OFFLINE",
            issue_type=9,
            environment=2,
            vNF=100.00,
            signed_xml="<NFe><infNFe Id='NFe35260911222333000181650010000000999123456781'></infNFe></NFe>",
        )
        self.db.add(doc)
        self.db.commit()

        # Chamada 1: Retorna Rejeição 204 (Duplicidade) ao tentar enviar o lote
        # Chamada 2: Consulta do Protocolo retorna cStat 100 com o protocolo oficial nProt 135260009999999
        resp_autorizacao = SefazResponse(
            success=False,
            status_code=204,
            reason="Rejeição: Duplicidade de NF-e com diferença na Chave de Acesso",
            raw_response_xml="<retEnviNFe><cStat>204</cStat></retEnviNFe>",
        )
        resp_consulta = SefazResponse(
            success=True,
            status_code=100,
            reason="Autorizado o uso da NF-e",
            protocol_number="135260009999999",
            digest_value="abc123digestvalue=",
            raw_response_xml="<retConsSitNFe><cStat>100</cStat><protNFe><infProt><nProt>135260009999999</nProt></infProt></protNFe></retConsSitNFe>",
        )
        mock_sefaz_send.side_effect = [resp_autorizacao, resp_consulta]

        # Executa reconciliação
        result = FiscalReconciler.reconcile_and_transmit_contingency_doc(self.db, doc)

        self.assertEqual(result.get("status"), "RECONCILED_AUTHORIZED")
        self.assertEqual(result.get("protocol"), "135260009999999")
        self.assertEqual(doc.status, NfeStatus.AUTHORIZED.value)
        self.assertEqual(doc.protocol_number, "135260009999999")
        self.assertIn("<nfeProc", doc.proc_xml)

    @patch("app.services.nfce_service.SefazServiceAdapter.send_request")
    def test_pos_sale_retry_idempotency(self, mock_sefaz_send):
        """Garante que chamadas duplicadas para a mesma venda no PDV
        não criam notas duplicadas nem realizam saltos indevidos na série fiscal.
        """
        mock_sefaz_send.return_value = SefazResponse(
            success=True,
            status_code=100,
            reason="Autorizado o uso da NF-e",
            protocol_number="135260001112223",
        )

        user_id = uuid.uuid4()
        sale = Sale(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            user_id=user_id,
            code="VND-IDEMP-001",
            status=SaleStatus.COMPLETED,
            subtotal=10.00,
            discount_amount=0.00,
            total_amount=10.00,
            items=[],
            payments=[],
        )
        self.db.add(sale)
        self.db.commit()

        # Primeira tentativa de emissão
        doc1 = NfceService.emit_nfce_for_sale(self.db, self.tenant_id, self.company_id, sale, user_id=user_id)
        
        # Segunda tentativa de emissão da MESMA venda
        doc2 = NfceService.emit_nfce_for_sale(self.db, self.tenant_id, self.company_id, sale, user_id=user_id)

        self.assertEqual(doc1.id, doc2.id)
        self.assertEqual(doc1.access_key, doc2.access_key)
        self.assertEqual(doc1.number, doc2.number)
