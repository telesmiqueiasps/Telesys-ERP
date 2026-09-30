import unittest
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.company import Company
from app.models.fiscal_update import (
    FiscalSchemaVersion,
    FiscalRuleVersion,
    FiscalUpdateAudit,
    FiscalUpdateStatus,
)
from app.schemas.fiscal_update import (
    FiscalSchemaVersionCreate,
    FiscalRuleVersionInput,
    FiscalRuleApplyRequest,
    FiscalRuleRejectRequest,
)
from app.services.fiscal_update_service import (
    register_technical_note_update,
    approve_and_apply_fiscal_update,
    reject_fiscal_update,
    get_pending_fiscal_updates,
    get_all_fiscal_schema_versions,
)


class TestFiscalUpdateCenter(unittest.TestCase):
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
            name="EMPRESA ATUALIZACAO FISCAL LTDA",
            cnpj="11.222.333/0001-81",
            state_registration="123456789",
        )
        self.db.add(self.company)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def test_seed_default_technical_notes_and_schemas(self):
        """Valida a semeadura inicial de Notas Técnicas com datas de Homologação e Produção."""
        versions = get_all_fiscal_schema_versions(self.db, self.tenant_id, self.company_id)
        self.assertGreaterEqual(len(versions), 2)
        
        nts = [v.technical_note.upper() for v in versions]
        self.assertTrue(any("2024.001" in nt for nt in nts))
        self.assertTrue(any("2023.004" in nt for nt in nts))

        nt_rtc = next(v for v in versions if "2024.001" in v.technical_note)
        self.assertEqual(nt_rtc.status, FiscalUpdateStatus.PENDING_APPROVAL.value)
        self.assertTrue(nt_rtc.requires_explicit_approval)
        self.assertIsNotNone(nt_rtc.homologation_effective_date)
        self.assertIsNotNone(nt_rtc.production_effective_date)

    def test_register_technical_note_update_non_silent(self):
        """Garante que novos registros nascem em PENDING_APPROVAL sem atualização silenciosa."""
        now_dt = datetime.now(timezone.utc)
        payload = FiscalSchemaVersionCreate(
            company_id=self.company_id,
            doc_model="55",
            schema_version="v4.01",
            technical_note="NT 2026.002 v1.00",
            title="NT 2026.002 - Novas Regras de Validação de Alíquotas RTC",
            description="Detalhamento das travas de alíquota máxima IBS/CBS",
            homologation_effective_date=now_dt + timedelta(days=10),
            production_effective_date=now_dt + timedelta(days=40),
            requires_explicit_approval=True,
            rules=[
                FiscalRuleVersionInput(
                    rule_code="RV_IBS_MAX_RATE",
                    rule_name="Validação da alíquota máxima do IBS",
                    scope="SEFAZ_VALIDATION",
                    new_value_json={"max_rate": 0.25},
                )
            ],
        )

        ver = register_technical_note_update(self.db, self.tenant_id, payload, self.user_id)

        self.assertIsNotNone(ver)
        self.assertEqual(ver.status, FiscalUpdateStatus.PENDING_APPROVAL.value)
        self.assertTrue(ver.requires_explicit_approval)
        self.assertIsNone(ver.applied_at)

        # Trilha de Auditoria
        audits = list(self.db.scalars(select(FiscalUpdateAudit).where(FiscalUpdateAudit.schema_version_id == ver.id)).all())
        self.assertEqual(len(audits), 1)
        self.assertEqual(audits[0].action, "REGISTERED")

    def test_approve_and_apply_fiscal_update_explicit_user_action(self):
        """Valida a aplicação explícita pelo usuário (user_id) gerando trilha de auditoria."""
        now_dt = datetime.now(timezone.utc)
        payload = FiscalSchemaVersionCreate(
            company_id=self.company_id,
            doc_model="55",
            schema_version="v4.01",
            technical_note="NT 2026.003 v1.00",
            title="NT 2026.003 - Novas Regras de Validação",
            homologation_effective_date=now_dt,
            production_effective_date=now_dt + timedelta(days=30),
            rules=[],
        )
        ver = register_technical_note_update(self.db, self.tenant_id, payload, self.user_id)

        # Aplicação explícita pelo usuário
        apply_req = FiscalRuleApplyRequest(
            user_id=self.user_id,
            environment="PRODUCTION",
            notes="Homologado com sucesso nos testes internos.",
        )
        applied_ver = approve_and_apply_fiscal_update(self.db, self.tenant_id, self.company_id, ver.id, apply_req)

        self.assertEqual(applied_ver.status, FiscalUpdateStatus.APPLIED.value)
        self.assertIsNotNone(applied_ver.applied_at)
        self.assertEqual(applied_ver.applied_by_user_id, self.user_id)

        # Audit Trail
        audits = list(self.db.scalars(select(FiscalUpdateAudit).where(FiscalUpdateAudit.schema_version_id == ver.id)).all())
        self.assertTrue(any(a.action == "APPLIED_PRODUCTION" for a in audits))

    def test_reject_fiscal_update_with_justification(self):
        """Valida a rejeição da atualização fiscal exigindo motivo/justificativa."""
        now_dt = datetime.now(timezone.utc)
        payload = FiscalSchemaVersionCreate(
            company_id=self.company_id,
            doc_model="55",
            schema_version="v4.01",
            technical_note="NT 2026.004 v1.00",
            title="NT 2026.004 - Regra com Conflito de Legislação",
            homologation_effective_date=now_dt,
            production_effective_date=now_dt + timedelta(days=30),
            rules=[],
        )
        ver = register_technical_note_update(self.db, self.tenant_id, payload, self.user_id)

        reject_req = FiscalRuleRejectRequest(
            user_id=self.user_id,
            rejection_reason="Rejeitado devido a divergência entre a NT e o decreto estadual vigente.",
        )
        rejected_ver = reject_fiscal_update(self.db, self.tenant_id, self.company_id, ver.id, reject_req)

        self.assertEqual(rejected_ver.status, FiscalUpdateStatus.REJECTED.value)
        self.assertIn("divergência entre a NT", rejected_ver.rejection_reason)

    def test_invalid_production_date_before_homologation(self):
        """Garante rejeição se a data de vigência em Produção for anterior à de Homologação."""
        now_dt = datetime.now(timezone.utc)
        payload_invalid_date = FiscalSchemaVersionCreate(
            company_id=self.company_id,
            doc_model="55",
            schema_version="v4.01",
            technical_note="NT 2026.005 v1.00",
            title="NT Invalida",
            homologation_effective_date=now_dt + timedelta(days=30),
            production_effective_date=now_dt,  # Data inválida (Produção antes de Homologação)
            rules=[],
        )

        with self.assertRaises(ValueError) as ctx:
            register_technical_note_update(self.db, self.tenant_id, payload_invalid_date, self.user_id)

        self.assertIn("Produção não pode ser anterior", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
