import unittest
import uuid
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.company import Company
from app.models.tenant import Tenant
from app.models.fiscal_operation import FiscalOperation, FiscalScenarioRule
from app.schemas.fiscal_operation import (
    FiscalOperationCreate,
    FiscalScenarioRuleCreate,
    FiscalScenarioMatchRequest,
)
from app.services.fiscal_operation import (
    get_company_fiscal_operations,
    create_fiscal_operation,
    resolve_fiscal_scenario,
)


class TestFiscalOperationsAndScenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # In-memory SQLite DB for fast test execution
        cls.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.Session()
        self.tenant_id = uuid.uuid4()
        self.company_id = uuid.uuid4()

    def tearDown(self):
        self.db.close()

    def test_seed_default_operations(self):
        ops = get_company_fiscal_operations(self.db, self.tenant_id, self.company_id)
        self.assertGreaterEqual(len(ops), 3)

        codes = [op.code for op in ops]
        self.assertIn("VENDA_ESTADO", codes)
        self.assertIn("VENDA_INTERESTADUAL", codes)
        self.assertIn("DEVOLUCAO_COMPRA", codes)

    def test_resolve_same_uf_sale(self):
        get_company_fiscal_operations(self.db, self.tenant_id, self.company_id)

        req = FiscalScenarioMatchRequest(
            operation_code="VENDA_ESTADO",
            operation_type="OUT",
            uf_origin="SP",
            uf_destination="SP",
            is_final_consumer=True,
            is_tax_contributor=False,
            doc_model="55",
            operation_date=date.today(),
        )

        res = resolve_fiscal_scenario(self.db, self.tenant_id, self.company_id, req)
        self.assertTrue(res.matched)
        self.assertEqual(res.cfop, "5102")
        self.assertTrue(res.affect_inventory)
        self.assertTrue(res.affect_financial)

    def test_resolve_different_uf_sale_final_consumer(self):
        get_company_fiscal_operations(self.db, self.tenant_id, self.company_id)

        # Consumidor final fora do estado -> deve casar com CFOP 6108
        req_fc = FiscalScenarioMatchRequest(
            operation_code="VENDA_INTERESTADUAL",
            operation_type="OUT",
            uf_origin="SP",
            uf_destination="RJ",
            is_final_consumer=True,
            is_tax_contributor=False,
            doc_model="55",
            operation_date=date.today(),
        )

        res_fc = resolve_fiscal_scenario(self.db, self.tenant_id, self.company_id, req_fc)
        self.assertTrue(res_fc.matched)
        self.assertEqual(res_fc.cfop, "6108")

        # Contribuinte revendedor fora do estado -> deve casar com CFOP 6102
        req_contrib = FiscalScenarioMatchRequest(
            operation_code="VENDA_INTERESTADUAL",
            operation_type="OUT",
            uf_origin="SP",
            uf_destination="RJ",
            is_final_consumer=False,
            is_tax_contributor=True,
            doc_model="55",
            operation_date=date.today(),
        )

        res_contrib = resolve_fiscal_scenario(self.db, self.tenant_id, self.company_id, req_contrib)
        self.assertTrue(res_contrib.matched)
        self.assertEqual(res_contrib.cfop, "6102")

    def test_effective_date_versioning(self):
        op_payload = FiscalOperationCreate(
            code="REMESSA_CONSERTO",
            name="Remessa para Conserto",
            operation_type="OUT",
            purpose=1,
            affect_inventory=True,
            affect_financial=False,
            allowed_doc_models="55",
            rules=[
                FiscalScenarioRuleCreate(
                    description="Regra Antiga (2020 a 2024)",
                    cfop="5915",
                    effective_from=date(2020, 1, 1),
                    effective_to=date(2024, 12, 31),
                    priority=10,
                ),
                FiscalScenarioRuleCreate(
                    description="Regra Nova (A partir de 2025)",
                    cfop="5916",
                    effective_from=date(2025, 1, 1),
                    effective_to=None,
                    priority=10,
                ),
            ],
        )
        create_fiscal_operation(self.db, self.tenant_id, self.company_id, op_payload)

        # Testar data em 2023 -> deve casar 5915
        req_2023 = FiscalScenarioMatchRequest(
            operation_code="REMESSA_CONSERTO",
            operation_type="OUT",
            uf_origin="MG",
            uf_destination="MG",
            is_final_consumer=False,
            is_tax_contributor=True,
            doc_model="55",
            operation_date=date(2023, 6, 15),
        )
        res_2023 = resolve_fiscal_scenario(self.db, self.tenant_id, self.company_id, req_2023)
        self.assertTrue(res_2023.matched)
        self.assertEqual(res_2023.cfop, "5915")

        # Testar data em 2026 -> deve casar 5916
        req_2026 = FiscalScenarioMatchRequest(
            operation_code="REMESSA_CONSERTO",
            operation_type="OUT",
            uf_origin="MG",
            uf_destination="MG",
            is_final_consumer=False,
            is_tax_contributor=True,
            doc_model="55",
            operation_date=date(2026, 3, 10),
        )
        res_2026 = resolve_fiscal_scenario(self.db, self.tenant_id, self.company_id, req_2026)
        self.assertTrue(res_2026.matched)
        self.assertEqual(res_2026.cfop, "5916")


if __name__ == "__main__":
    unittest.main()
