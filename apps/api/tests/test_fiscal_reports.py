import unittest
import uuid
from datetime import datetime, timezone, date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.company import Company
from app.models.company_fiscal import FiscalCompanyConfig
from app.models.nfe_document import NfeDocument, NfeItem, NfeStatus
from app.models.fiscal_event import FiscalEvent, FiscalInutilization
from app.schemas.fiscal_report import FiscalReportFilterRequest
from app.services.fiscal_report_service import generate_fiscal_report, export_fiscal_report_csv


class TestFiscalReports(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.Session()
        self.tenant_id = uuid.uuid4()
        self.company_id = uuid.uuid4()

        # Empresa Emissora
        self.company = Company(
            id=self.company_id,
            tenant_id=self.tenant_id,
            name="EMPRESA RELATORIOS FISCAIS LTDA",
            cnpj="11.222.333/0001-81",
            state_registration="123456789",
        )
        self.db.add(self.company)

        # Configuração Fiscal
        self.fiscal_config = FiscalCompanyConfig(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            crt=1,
            tax_regime="SIMPLES_NACIONAL",
        )
        self.db.add(self.fiscal_config)

        # 1. NF-e Emitida Autorizada (Saída, Venda, Modelo 55)
        self.doc_emitted = NfeDocument(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            access_key="35260911222333000181550010000001001987654321",
            number=100,
            series=1,
            model="55",
            nature_of_operation="Venda no Estado",
            operation_type_nfe=1,  # Saída
            purpose=1,  # Normal
            issue_type=1,
            environment=2,
            status=NfeStatus.AUTHORIZED.value,
            issuer_cnpj=self.company.cnpj,
            issuer_name=self.company.name,
            issuer_uf="SP",
            recipient_cnpj_cpf="99888777000199",
            recipient_name="CLIENTE COMPRADOR LTDA",
            recipient_uf="SP",
            vProd=1000.00,
            vBC=1000.00,
            vICMS=180.00,
            vPIS=16.50,
            vCOFINS=76.00,
            vNF=1000.00,
        )
        item_emitted = NfeItem(
            id=uuid.uuid4(),
            nfe_id=self.doc_emitted.id,
            item_number=1,
            product_code="PROD-01",
            description="Produto Teste Saida",
            ncm="84713012",
            cfop="5102",
            uCom="UN",
            qCom=1.0,
            vUnCom=1000.00,
            vProd=1000.00,
            uTrib="UN",
            qTrib=1.0,
            vUnTrib=1000.00,
            tax_snapshot_json={
                "icms": {"cst_csosn": "00", "vBC_ICMS": 1000.0, "vICMS": 180.0},
                "pis": {"cst_pis": "01", "vPIS": 16.5},
                "cofins": {"cst_cofins": "01", "vCOFINS": 76.0},
                "rtc": {"vBC_IBS": 1000.0, "vIBS": 1.5, "vBC_CBS": 1000.0, "vCBS": 9.0},
            },
        )
        self.doc_emitted.items.append(item_emitted)
        self.db.add(self.doc_emitted)

        # 2. NF-e Recebida (Entrada, Compra, Modelo 55)
        self.doc_received = NfeDocument(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            access_key="35260999888777000199550010000002001123456789",
            number=200,
            series=1,
            model="55",
            nature_of_operation="Compra para Comercialização",
            operation_type_nfe=0,  # Entrada
            purpose=1,
            issue_type=1,
            environment=2,
            status=NfeStatus.AUTHORIZED.value,
            issuer_cnpj="99888777000199",
            issuer_name="FORNECEDOR MATRIZ SA",
            issuer_uf="SP",
            recipient_cnpj_cpf=self.company.cnpj,
            recipient_name=self.company.name,
            recipient_uf="SP",
            vProd=500.00,
            vBC=500.00,
            vICMS=90.00,
            vNF=500.00,
        )
        item_received = NfeItem(
            id=uuid.uuid4(),
            nfe_id=self.doc_received.id,
            item_number=1,
            product_code="PROD-02",
            description="Materia Prima Entrada",
            ncm="84713012",
            cfop="1102",
            uCom="UN",
            qCom=1.0,
            vUnCom=500.00,
            vProd=500.00,
            uTrib="UN",
            qTrib=1.0,
            vUnTrib=500.00,
            tax_snapshot_json={
                "icms": {"cst_csosn": "00", "vBC_ICMS": 500.0, "vICMS": 90.0},
                "rtc": {"vBC_IBS": 500.0, "vIBS": 0.75, "vBC_CBS": 500.0, "vCBS": 4.5},
            },
        )
        self.doc_received.items.append(item_received)
        self.db.add(self.doc_received)

        # 3. NF-e Cancelada
        self.doc_cancelled = NfeDocument(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            access_key="35260911222333000181550010000003001987654321",
            number=300,
            series=1,
            model="55",
            nature_of_operation="Venda de Mercadoria",
            operation_type_nfe=1,
            purpose=1,
            issue_type=1,
            environment=2,
            status=NfeStatus.CANCELLED.value,
            issuer_cnpj=self.company.cnpj,
            issuer_name=self.company.name,
            issuer_uf="SP",
            recipient_cnpj_cpf="99888777000199",
            recipient_name="CLIENTE CANCELADO LTDA",
            recipient_uf="SP",
            vProd=300.00,
            vNF=300.00,
            sefaz_reason="Cancelamento homologado",
        )
        self.db.add(self.doc_cancelled)

        # 4. NF-e de Devolução (finNFe 4)
        self.doc_return = NfeDocument(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            access_key="35260911222333000181550010000004001987654321",
            number=400,
            series=1,
            model="55",
            nature_of_operation="Devolução de Compra",
            operation_type_nfe=1,
            purpose=4,  # Devolução
            issue_type=1,
            environment=2,
            status=NfeStatus.AUTHORIZED.value,
            issuer_cnpj=self.company.cnpj,
            issuer_name=self.company.name,
            issuer_uf="SP",
            recipient_cnpj_cpf="99888777000199",
            recipient_name="FORNECEDOR DESTINATARIO LTDA",
            recipient_uf="SP",
            vProd=200.00,
            vNF=200.00,
            referenced_nfe_key=self.doc_received.access_key,
        )
        item_return = NfeItem(
            id=uuid.uuid4(),
            nfe_id=self.doc_return.id,
            item_number=1,
            product_code="PROD-02",
            description="Devolução de Materia Prima",
            ncm="84713012",
            cfop="5202",
            uCom="UN",
            qCom=1.0,
            vUnCom=200.00,
            vProd=200.00,
            uTrib="UN",
            qTrib=1.0,
            vUnTrib=200.00,
            tax_snapshot_json={"icms": {"cst_csosn": "00"}},
        )
        self.doc_return.items.append(item_return)
        self.db.add(self.doc_return)

        # 5. Inutilização Registrada
        self.inut = FiscalInutilization(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            model="55",
            series=1,
            year=2026,
            start_number=500,
            end_number=510,
            justification="Quebra de sequência numérica de teste",
            sefaz_status_code=102,
            sefaz_reason="Inutilização de número homologado",
        )
        self.db.add(self.inut)

        # 6. Evento Fiscal Registrado (CC-e)
        self.event = FiscalEvent(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            nfe_id=self.doc_emitted.id,
            access_key=self.doc_emitted.access_key,
            event_type="110110",
            event_name="Carta de Correção Eletrônica",
            seq_number=1,
            justification_or_correction="Correção no transporte e observação fiscal do item 1",
            sefaz_status_code=135,
            sefaz_reason="Evento registrado e vinculado a NF-e",
        )
        self.db.add(self.event)

        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def test_emitted_notes_report(self):
        """Valida relatório de Notas Emitidas (Saídas)."""
        req = FiscalReportFilterRequest(
            company_id=self.company_id,
            report_type="EMITTED",
        )
        rep = generate_fiscal_report(self.db, self.tenant_id, req)

        self.assertEqual(rep.report_type, "EMITTED")
        self.assertGreaterEqual(len(rep.rows), 1)
        self.assertTrue(any(r.document_number == "100" for r in rep.rows))
        self.assertGreater(rep.totals.total_vProd, 0.0)

    def test_received_notes_report(self):
        """Valida relatório de Notas Recebidas (Entradas)."""
        req = FiscalReportFilterRequest(
            company_id=self.company_id,
            report_type="RECEIVED",
        )
        rep = generate_fiscal_report(self.db, self.tenant_id, req)

        self.assertEqual(rep.report_type, "RECEIVED")
        self.assertEqual(len(rep.rows), 1)
        self.assertEqual(rep.rows[0].document_number, "200")
        self.assertEqual(rep.rows[0].operation_type, "ENTRADA")

    def test_cancelled_notes_report(self):
        """Valida relatório de Notas Canceladas."""
        req = FiscalReportFilterRequest(
            company_id=self.company_id,
            report_type="CANCELLED",
        )
        rep = generate_fiscal_report(self.db, self.tenant_id, req)

        self.assertEqual(rep.report_type, "CANCELLED")
        self.assertEqual(len(rep.rows), 1)
        self.assertEqual(rep.rows[0].document_number, "300")
        self.assertEqual(rep.rows[0].status, "CANCELLED")

    def test_inutilized_notes_report(self):
        """Valida relatório de Faixas Inutilizadas."""
        req = FiscalReportFilterRequest(
            company_id=self.company_id,
            report_type="INUTILIZED",
        )
        rep = generate_fiscal_report(self.db, self.tenant_id, req)

        self.assertEqual(rep.report_type, "INUTILIZED")
        self.assertEqual(len(rep.rows), 1)
        self.assertEqual(rep.rows[0].document_number, "500 a 510")
        self.assertIn("Quebra de sequência", rep.rows[0].notes_or_reason)

    def test_events_report(self):
        """Valida relatório de Eventos Fiscais."""
        req = FiscalReportFilterRequest(
            company_id=self.company_id,
            report_type="EVENTS",
        )
        rep = generate_fiscal_report(self.db, self.tenant_id, req)

        self.assertEqual(rep.report_type, "EVENTS")
        self.assertEqual(len(rep.rows), 1)
        self.assertEqual(rep.rows[0].access_key, self.doc_emitted.access_key)
        self.assertIn("Carta de Correção", rep.rows[0].operation_type)

    def test_by_cfop_report(self):
        """Valida relatório agrupado por CFOP."""
        req = FiscalReportFilterRequest(
            company_id=self.company_id,
            report_type="BY_CFOP",
        )
        rep = generate_fiscal_report(self.db, self.tenant_id, req)

        self.assertEqual(rep.report_type, "BY_CFOP")
        self.assertGreaterEqual(len(rep.grouped_rows), 1)
        cfops = [g.key_code for g in rep.grouped_rows]
        self.assertIn("5102", cfops)

    def test_by_cst_report(self):
        """Valida relatório agrupado por CST / CSOSN."""
        req = FiscalReportFilterRequest(
            company_id=self.company_id,
            report_type="BY_CST",
        )
        rep = generate_fiscal_report(self.db, self.tenant_id, req)

        self.assertEqual(rep.report_type, "BY_CST")
        self.assertGreaterEqual(len(rep.grouped_rows), 1)
        csts = [g.key_code for g in rep.grouped_rows]
        self.assertIn("00", csts)

    def test_returns_report(self):
        """Valida relatório de Devoluções de Compra/Venda (finNFe 4)."""
        req = FiscalReportFilterRequest(
            company_id=self.company_id,
            report_type="RETURNS",
        )
        rep = generate_fiscal_report(self.db, self.tenant_id, req)

        self.assertEqual(rep.report_type, "RETURNS")
        self.assertEqual(len(rep.rows), 1)
        self.assertEqual(rep.rows[0].document_number, "400")
        self.assertEqual(rep.rows[0].purpose, "4")

    def test_csv_export_format(self):
        """Valida a exportação formatada em CSV."""
        req = FiscalReportFilterRequest(
            company_id=self.company_id,
            report_type="EMITTED",
            export_format="csv",
        )
        rep = generate_fiscal_report(self.db, self.tenant_id, req)

        self.assertIsNotNone(rep.csv_content)
        self.assertIn("RELATORIO FISCAL TELE-SYS ERP", rep.csv_content)
        self.assertIn("DETALHAMENTO DOS DOCUMENTOS", rep.csv_content)
        self.assertIn("100", rep.csv_content)

        # Valida função direta export_fiscal_report_csv
        csv_direct = export_fiscal_report_csv(rep)
        self.assertIn("TOTAIS CONSOLIDADOS", csv_direct)


if __name__ == "__main__":
    unittest.main()
