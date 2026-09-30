import unittest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.company import Company
from app.services.fiscal_homologation_service import run_fiscal_homologation_suite


class TestFiscalHomologationSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.Session()
        self.tenant_id = uuid.uuid4()
        self.company_id = uuid.uuid4()

        # Empresa Emissora para Homologação
        self.company = Company(
            id=self.company_id,
            tenant_id=self.tenant_id,
            name="TELESYS SOFTWARE E AUTOMAÇÃO LTDA",
            cnpj="11.222.333/0001-81",
            state_registration="123456789",
        )
        self.db.add(self.company)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def test_run_full_fiscal_homologation_suite_success(self):
        """Valida a execução completa da Suíte de Homologação cobrindo os 12 módulos com 100% de sucesso."""
        report = run_fiscal_homologation_suite(
            db=self.db,
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            environment="2",
        )

        self.assertIsNotNone(report)
        self.assertTrue(report.is_fully_homologated)
        self.assertEqual(report.total_modules, 12)
        self.assertEqual(report.total_tests, 12)
        self.assertEqual(report.passed_tests, 12)
        self.assertEqual(report.failed_tests, 0)
        self.assertEqual(report.success_rate_percent, 100.0)
        self.assertEqual(len(report.results), 12)

        # Módulos esperados
        expected_modules = {
            "CERTIFICADO",
            "AUTORIZACAO",
            "REJEICAO",
            "CANCELAMENTO",
            "CCE",
            "INUTILIZACAO",
            "CONTINGENCIA",
            "DUPLICIDADE",
            "DEVOLUCAO",
            "ENTRADA_XML",
            "NFSE",
            "RECONCILIACAO",
        }
        actual_modules = {item.module_code for item in report.results}
        self.assertEqual(expected_modules, actual_modules)

        # Verifica se todos os itens de homologação possuem passed=True
        for result in report.results:
            self.assertTrue(result.passed, f"Módulo {result.module_code} falhou: {result.details}")
            self.assertIsNotNone(result.details, f"Módulo {result.module_code} não possui detalhes técnicos de validação.")

    def test_homologation_suite_module_specific_assertions(self):
        """Verifica detalhes específicos dos testes de cada módulo fiscal."""
        report = run_fiscal_homologation_suite(
            db=self.db,
            tenant_id=self.tenant_id,
            company_id=self.company_id,
            environment="2",
        )

        results_by_module = {item.module_code: item for item in report.results}

        # 1. Certificado Digital A1 (Cryptografado e Validado)
        self.assertTrue(results_by_module["CERTIFICADO"].passed)
        self.assertIn("criptografado", results_by_module["CERTIFICADO"].details)

        # 2. Autorização (55/65)
        self.assertTrue(results_by_module["AUTORIZACAO"].passed)
        self.assertIn("cStat 100", results_by_module["AUTORIZACAO"].details)

        # 3. Rejeição SEFAZ (204 e 539)
        self.assertTrue(results_by_module["REJEICAO"].passed)

        # 4. Cancelamento (cStat 135)
        self.assertTrue(results_by_module["CANCELAMENTO"].passed)

        # 5. Carta de Correção (CC-e)
        self.assertTrue(results_by_module["CCE"].passed)

        # 6. Inutilização
        self.assertTrue(results_by_module["INUTILIZACAO"].passed)

        # 7. Contingência
        self.assertTrue(results_by_module["CONTINGENCIA"].passed)

        # 8. Duplicidade
        self.assertTrue(results_by_module["DUPLICIDADE"].passed)

        # 9. Devolução (finNFe 4)
        self.assertTrue(results_by_module["DEVOLUCAO"].passed)

        # 10. Entrada XML
        self.assertTrue(results_by_module["ENTRADA_XML"].passed)

        # 11. NFS-e Padrão Nacional
        self.assertTrue(results_by_module["NFSE"].passed)

        # 12. Reconciliação / Idempotência
        self.assertTrue(results_by_module["RECONCILIACAO"].passed)


if __name__ == "__main__":
    unittest.main()
