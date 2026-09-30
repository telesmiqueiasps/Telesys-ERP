import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.company import Company
from app.models.fiscal_update import (
    FiscalSchemaVersion,
    FiscalRuleVersion,
    FiscalUpdateAudit,
    FiscalUpdateStatus,
)
from app.models.audit import AuditLog
from app.schemas.fiscal_update import (
    FiscalSchemaVersionCreate,
    FiscalRuleApplyRequest,
    FiscalRuleRejectRequest,
)


def register_technical_note_update(
    db: Session,
    tenant_id: uuid.UUID,
    payload: FiscalSchemaVersionCreate,
    user_id: Optional[uuid.UUID] = None,
) -> FiscalSchemaVersion:
    """
    Registra nova Nota Técnica / Versão de Schema SEFAZ no Centro de Atualizações Fiscais.
    REGRA CRÍTICA: Não atualiza silenciosamente. O registro nasce em estado PENDING_APPROVAL.
    """
    company = db.scalar(
        select(Company).where(Company.id == payload.company_id, Company.tenant_id == tenant_id)
    )
    if not company:
        raise ValueError("Empresa informada não existe ou não pertence ao tenant.")

    if payload.production_effective_date < payload.homologation_effective_date:
        raise ValueError("A data de vigência em Produção não pode ser anterior à data de vigência em Homologação.")

    rules_changes_map = {
        rule.rule_code: {
            "name": rule.rule_name,
            "scope": rule.scope,
            "old": rule.old_value_json,
            "new": rule.new_value_json,
            "breaking": rule.is_breaking_change,
        }
        for rule in payload.rules
    }

    schema_ver = FiscalSchemaVersion(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=payload.company_id,
        doc_model=payload.doc_model,
        schema_version=payload.schema_version,
        technical_note=payload.technical_note.upper().strip(),
        title=payload.title,
        description=payload.description,
        homologation_effective_date=payload.homologation_effective_date,
        production_effective_date=payload.production_effective_date,
        status=FiscalUpdateStatus.PENDING_APPROVAL.value,
        requires_explicit_approval=True,
        rules_changes_json=rules_changes_map,
    )

    for r_in in payload.rules:
        rule_ent = FiscalRuleVersion(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            company_id=payload.company_id,
            schema_version_id=schema_ver.id,
            rule_code=r_in.rule_code,
            rule_name=r_in.rule_name,
            scope=r_in.scope,
            old_value_json=r_in.old_value_json,
            new_value_json=r_in.new_value_json,
            is_breaking_change=r_in.is_breaking_change,
            requires_user_confirmation=True,
            status=FiscalUpdateStatus.PENDING_APPROVAL.value,
        )
        schema_ver.rules.append(rule_ent)

    db.add(schema_ver)

    if user_id:
        audit_rec = FiscalUpdateAudit(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            company_id=payload.company_id,
            schema_version_id=schema_ver.id,
            action="REGISTERED",
            user_id=user_id,
            details_json={
                "technical_note": schema_ver.technical_note,
                "title": schema_ver.title,
                "homologation_date": schema_ver.homologation_effective_date.isoformat(),
                "production_date": schema_ver.production_effective_date.isoformat(),
            },
        )
        db.add(audit_rec)

    db.commit()
    db.refresh(schema_ver)
    return schema_ver


def approve_and_apply_fiscal_update(
    db: Session,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    version_id: uuid.UUID,
    payload: FiscalRuleApplyRequest,
) -> FiscalSchemaVersion:
    """
    Aplica explicitamente uma Nota Técnica ou atualização fiscal para Homologação ou Produção.
    Exige confirmação do usuário (user_id) impedindo atualizações silenciosas.
    """
    schema_ver = db.scalar(
        select(FiscalSchemaVersion).where(
            FiscalSchemaVersion.id == version_id,
            FiscalSchemaVersion.company_id == company_id,
            FiscalSchemaVersion.tenant_id == tenant_id,
        )
    )
    if not schema_ver:
        raise ValueError("Versão de schema/Nota Técnica não encontrada.")

    if schema_ver.status == FiscalUpdateStatus.REJECTED.value:
        raise ValueError("Não é possível aplicar uma atualização fiscal que foi REJEITADA. Crie um novo registro de versão.")

    schema_ver.status = FiscalUpdateStatus.APPLIED.value
    schema_ver.applied_at = datetime.now(timezone.utc)
    schema_ver.applied_by_user_id = payload.user_id

    for r in schema_ver.rules:
        r.status = FiscalUpdateStatus.APPLIED.value

    # Registro de Auditoria do Centro de Atualizações Fiscais
    update_audit = FiscalUpdateAudit(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=company_id,
        schema_version_id=schema_ver.id,
        action=f"APPLIED_{payload.environment.upper()}",
        user_id=payload.user_id,
        details_json={
            "applied_at": schema_ver.applied_at.isoformat(),
            "environment": payload.environment,
            "technical_note": schema_ver.technical_note,
            "notes": payload.notes,
        },
    )
    db.add(update_audit)

    # Registro no AuditLog Geral do Sistema
    sys_audit = AuditLog(
        tenant_id=tenant_id,
        company_id=company_id,
        user_id=payload.user_id,
        action="FISCAL_UPDATE_APPLIED",
        entity="fiscal_schema_version",
        entity_id=schema_ver.id,
        after_data=json.dumps({
            "technical_note": schema_ver.technical_note,
            "schema_version": schema_ver.schema_version,
            "environment": payload.environment,
            "applied_at": schema_ver.applied_at.isoformat(),
        }),
    )
    db.add(sys_audit)

    db.commit()
    db.refresh(schema_ver)
    return schema_ver


def reject_fiscal_update(
    db: Session,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    version_id: uuid.UUID,
    payload: FiscalRuleRejectRequest,
) -> FiscalSchemaVersion:
    """
    Rejeita a aplicação de uma Nota Técnica / atualização fiscal com justificativa auditável.
    """
    schema_ver = db.scalar(
        select(FiscalSchemaVersion).where(
            FiscalSchemaVersion.id == version_id,
            FiscalSchemaVersion.company_id == company_id,
            FiscalSchemaVersion.tenant_id == tenant_id,
        )
    )
    if not schema_ver:
        raise ValueError("Versão de schema/Nota Técnica não encontrada.")

    reason_text = payload.rejection_reason.strip()
    if len(reason_text) < 10:
        raise ValueError("A justificativa da rejeição é obrigatória e deve conter no mínimo 10 caracteres.")

    schema_ver.status = FiscalUpdateStatus.REJECTED.value
    schema_ver.rejection_reason = reason_text

    for r in schema_ver.rules:
        r.status = FiscalUpdateStatus.REJECTED.value

    update_audit = FiscalUpdateAudit(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=company_id,
        schema_version_id=schema_ver.id,
        action="REJECTED",
        user_id=payload.user_id,
        details_json={
            "rejected_at": datetime.now(timezone.utc).isoformat(),
            "reason": reason_text,
            "technical_note": schema_ver.technical_note,
        },
    )
    db.add(update_audit)

    db.commit()
    db.refresh(schema_ver)
    return schema_ver


def get_pending_fiscal_updates(
    db: Session,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
) -> List[FiscalSchemaVersion]:
    """
    Retorna a lista de atualizações fiscais pendentes de aprovação prévia pelo usuário.
    """
    return list(
        db.scalars(
            select(FiscalSchemaVersion)
            .where(
                FiscalSchemaVersion.company_id == company_id,
                FiscalSchemaVersion.tenant_id == tenant_id,
                FiscalSchemaVersion.status == FiscalUpdateStatus.PENDING_APPROVAL.value,
            )
            .order_by(FiscalSchemaVersion.production_effective_date.asc())
        ).all()
    )


def get_all_fiscal_schema_versions(
    db: Session,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
) -> List[FiscalSchemaVersion]:
    """
    Retorna o histórico completo de versões de schemas e Notas Técnicas cadastradas.
    Se não houver atualizações cadastradas, faz a semeadura das NTs padrões do mercado.
    """
    versions = list(
        db.scalars(
            select(FiscalSchemaVersion)
            .where(
                FiscalSchemaVersion.company_id == company_id,
                FiscalSchemaVersion.tenant_id == tenant_id,
            )
            .order_by(FiscalSchemaVersion.created_at.desc())
        ).all()
    )

    if not versions:
        versions = seed_default_technical_notes_and_schemas(db, tenant_id, company_id)

    return versions


def seed_default_technical_notes_and_schemas(
    db: Session,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
) -> List[FiscalSchemaVersion]:
    """
    Cadastra as Notas Técnicas e Schemas de referência da SEFAZ com vigências de Homologação e Produção.
    """
    now_dt = datetime.now(timezone.utc)

    # 1. NT 2024.001 v1.20 (Reforma Tributária IBS / CBS)
    nt_2024_001 = FiscalSchemaVersion(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=company_id,
        doc_model="55",
        schema_version="RTC_2026.1",
        technical_note="NT 2024.001 v1.20",
        title="Nota Técnica NT 2024.001 - Campos e Validações da Reforma Tributária (IBS/CBS)",
        description="Publicação dos campos de Classificação Tributária, CST IBS/CBS, alíquotas repartidas e reduções de base de cálculo.",
        homologation_effective_date=now_dt - timedelta(days=60),
        production_effective_date=now_dt + timedelta(days=90),
        status=FiscalUpdateStatus.PENDING_APPROVAL.value,
        requires_explicit_approval=True,
        rules_changes_json={
            "RULE_IBS_CBS_CALC": {
                "name": "Cálculo de IBS/CBS com Redução de BC",
                "scope": "TAX_CALCULATION",
                "new": {"pIBS_State": 0.10, "pIBS_Mun": 0.05, "pCBS": 0.90},
                "breaking": False,
            }
        },
    )
    r1 = FiscalRuleVersion(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=company_id,
        schema_version_id=nt_2024_001.id,
        rule_code="RULE_IBS_CBS_CALC",
        rule_name="Cálculo de IBS/CBS com Redução de BC",
        scope="TAX_CALCULATION",
        new_value_json={"pIBS_State": 0.10, "pIBS_Mun": 0.05, "pCBS": 0.90},
        is_breaking_change=False,
        requires_user_confirmation=True,
        status=FiscalUpdateStatus.PENDING_APPROVAL.value,
    )
    nt_2024_001.rules.append(r1)

    # 2. NT 2023.004 v1.11 (Alterações no evento de conciliação e contingência)
    nt_2023_004 = FiscalSchemaVersion(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=company_id,
        doc_model="65",
        schema_version="v4.00",
        technical_note="NT 2023.004 v1.11",
        title="Nota Técnica NT 2023.004 - Contingência NFC-e e QR Code v2.0",
        description="Aprimoramento das regras de transmissão offline e validação de QR Code com hash SHA1.",
        homologation_effective_date=now_dt - timedelta(days=180),
        production_effective_date=now_dt - timedelta(days=30),
        status=FiscalUpdateStatus.APPLIED.value,
        requires_explicit_approval=True,
        applied_at=now_dt - timedelta(days=30),
        rules_changes_json={
            "RULE_QRCODE_SHA1": {
                "name": "Geração do QR Code NFC-e com Digest SHA1",
                "scope": "SEFAZ_VALIDATION",
                "new": {"hash": "SHA1", "param_cStat": 100},
                "breaking": False,
            }
        },
    )
    r2 = FiscalRuleVersion(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=company_id,
        schema_version_id=nt_2023_004.id,
        rule_code="RULE_QRCODE_SHA1",
        rule_name="Geração do QR Code NFC-e com Digest SHA1",
        scope="SEFAZ_VALIDATION",
        new_value_json={"hash": "SHA1", "param_cStat": 100},
        is_breaking_change=False,
        requires_user_confirmation=True,
        status=FiscalUpdateStatus.APPLIED.value,
    )
    nt_2023_004.rules.append(r2)

    db.add_all([nt_2024_001, nt_2023_004])
    db.commit()
    db.refresh(nt_2024_001)
    db.refresh(nt_2023_004)

    return [nt_2024_001, nt_2023_004]
