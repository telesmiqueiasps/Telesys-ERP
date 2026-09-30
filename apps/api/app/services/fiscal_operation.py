import uuid
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_

from app.models.fiscal_operation import FiscalOperation, FiscalScenarioRule
from app.schemas.fiscal_operation import (
    FiscalOperationCreate,
    FiscalOperationUpdate,
    FiscalScenarioRuleCreate,
    FiscalScenarioRuleUpdate,
    FiscalScenarioMatchRequest,
    FiscalScenarioMatchResult,
)


def get_company_fiscal_operations(
    db: Session, tenant_id: uuid.UUID, company_id: uuid.UUID
) -> List[FiscalOperation]:
    """
    Retorna a lista de operações fiscais da empresa.
    Se a empresa não possuir operações cadastradas, faz a semeadura das operações padrões do Brasil.
    """
    ops = list(
        db.scalars(
            select(FiscalOperation)
            .where(
                FiscalOperation.company_id == company_id,
                FiscalOperation.tenant_id == tenant_id,
            )
            .order_by(FiscalOperation.code.asc())
        ).all()
    )

    if not ops:
        ops = seed_default_fiscal_operations(db, tenant_id, company_id)

    return ops


def seed_default_fiscal_operations(
    db: Session, tenant_id: uuid.UUID, company_id: uuid.UUID
) -> List[FiscalOperation]:
    """
    Cadastra as operações fiscais e cenários padrões de mercado para a empresa.
    """
    op_venda_int = FiscalOperation(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=company_id,
        code="VENDA_ESTADO",
        name="Venda de Mercadoria no Estado",
        operation_type="OUT",
        purpose=1,
        affect_inventory=True,
        affect_financial=True,
        allowed_doc_models="55,65",
        description="Venda interna de mercadorias no mesmo estado da matriz/filial.",
        is_active=True,
    )

    rule_venda_int = FiscalScenarioRule(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=company_id,
        fiscal_operation_id=op_venda_int.id,
        description="Venda Interna Padrão (CFOP 5102)",
        is_same_uf=True,
        cfop="5102",
        effective_from=date(2020, 1, 1),
        priority=10,
        is_active=True,
    )
    op_venda_int.rules.append(rule_venda_int)

    op_venda_ext = FiscalOperation(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=company_id,
        code="VENDA_INTERESTADUAL",
        name="Venda Interestadual de Mercadoria",
        operation_type="OUT",
        purpose=1,
        affect_inventory=True,
        affect_financial=True,
        allowed_doc_models="55,65",
        description="Venda de mercadorias para destinatários localizados em outros estados.",
        is_active=True,
    )

    rule_venda_ext_contrib = FiscalScenarioRule(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=company_id,
        fiscal_operation_id=op_venda_ext.id,
        description="Venda Interestadual para Contribuinte (CFOP 6102)",
        is_same_uf=False,
        is_final_consumer=False,
        cfop="6102",
        effective_from=date(2020, 1, 1),
        priority=10,
        is_active=True,
    )

    rule_venda_ext_ncontrib = FiscalScenarioRule(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=company_id,
        fiscal_operation_id=op_venda_ext.id,
        description="Venda Interestadual Consumidor Final (CFOP 6108)",
        is_same_uf=False,
        is_final_consumer=True,
        cfop="6108",
        effective_from=date(2020, 1, 1),
        priority=5,
        is_active=True,
    )
    op_venda_ext.rules.extend([rule_venda_ext_contrib, rule_venda_ext_ncontrib])

    op_devolucao = FiscalOperation(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=company_id,
        code="DEVOLUCAO_COMPRA",
        name="Devolução de Compra de Mercadoria",
        operation_type="OUT",
        purpose=4,  # Devolução
        affect_inventory=True,
        affect_financial=True,
        allowed_doc_models="55",
        description="Devolução de compras de fornecedores no estado ou fora dele.",
        is_active=True,
    )

    rule_dev_int = FiscalScenarioRule(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=company_id,
        fiscal_operation_id=op_devolucao.id,
        description="Devolução de Compra Interna (CFOP 5202)",
        is_same_uf=True,
        cfop="5202",
        effective_from=date(2020, 1, 1),
        priority=10,
        is_active=True,
    )

    rule_dev_ext = FiscalScenarioRule(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=company_id,
        fiscal_operation_id=op_devolucao.id,
        description="Devolução de Compra Interestadual (CFOP 6202)",
        is_same_uf=False,
        cfop="6202",
        effective_from=date(2020, 1, 1),
        priority=10,
        is_active=True,
    )
    # Devolução de Venda
    op_dev_venda = FiscalOperation(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=company_id,
        code="DEVOLUCAO_VENDA",
        name="Devolução de Venda de Mercadoria",
        operation_type="IN",
        purpose=4,  # Devolução
        affect_inventory=True,
        affect_financial=False,
        allowed_doc_models="55",
        description="Recebimento em devolução de venda emitida anteriormente para cliente.",
        is_active=True,
    )
    rule_dev_venda_int = FiscalScenarioRule(
        id=uuid.uuid4(), tenant_id=tenant_id, company_id=company_id,
        fiscal_operation_id=op_dev_venda.id, description="Devolução de Venda Interna (CFOP 1202)",
        is_same_uf=True, cfop="1202", effective_from=date(2020, 1, 1), priority=10, is_active=True
    )
    rule_dev_venda_ext = FiscalScenarioRule(
        id=uuid.uuid4(), tenant_id=tenant_id, company_id=company_id,
        fiscal_operation_id=op_dev_venda.id, description="Devolução de Venda Interestadual (CFOP 2202)",
        is_same_uf=False, cfop="2202", effective_from=date(2020, 1, 1), priority=10, is_active=True
    )
    op_dev_venda.rules.extend([rule_dev_venda_int, rule_dev_venda_ext])

    # Remessa para Conserto
    op_rem_conserto = FiscalOperation(
        id=uuid.uuid4(), tenant_id=tenant_id, company_id=company_id,
        code="REMESSA_CONSERTO", name="Remessa para Conserto ou Reparo",
        operation_type="OUT", purpose=1, affect_inventory=True, affect_financial=False,
        allowed_doc_models="55", description="Remessa de bem ou equipamento para conserto em terceiros.", is_active=True
    )
    rule_rem_cons_int = FiscalScenarioRule(
        id=uuid.uuid4(), tenant_id=tenant_id, company_id=company_id, fiscal_operation_id=op_rem_conserto.id,
        description="Remessa Conserto Interna (CFOP 5915)", is_same_uf=True, cfop="5915", effective_from=date(2020, 1, 1), priority=10, is_active=True
    )
    rule_rem_cons_ext = FiscalScenarioRule(
        id=uuid.uuid4(), tenant_id=tenant_id, company_id=company_id, fiscal_operation_id=op_rem_conserto.id,
        description="Remessa Conserto Interestadual (CFOP 6915)", is_same_uf=False, cfop="6915", effective_from=date(2020, 1, 1), priority=10, is_active=True
    )
    op_rem_conserto.rules.extend([rule_rem_cons_int, rule_rem_cons_ext])

    # Remessa para Demonstração
    op_rem_demo = FiscalOperation(
        id=uuid.uuid4(), tenant_id=tenant_id, company_id=company_id,
        code="REMESSA_DEMONSTRACAO", name="Remessa para Demonstração",
        operation_type="OUT", purpose=1, affect_inventory=True, affect_financial=False,
        allowed_doc_models="55", description="Remessa de produtos para demonstração comercial.", is_active=True
    )
    rule_rem_demo_int = FiscalScenarioRule(
        id=uuid.uuid4(), tenant_id=tenant_id, company_id=company_id, fiscal_operation_id=op_rem_demo.id,
        description="Remessa Demonstração Interna (CFOP 5912)", is_same_uf=True, cfop="5912", effective_from=date(2020, 1, 1), priority=10, is_active=True
    )
    rule_rem_demo_ext = FiscalScenarioRule(
        id=uuid.uuid4(), tenant_id=tenant_id, company_id=company_id, fiscal_operation_id=op_rem_demo.id,
        description="Remessa Demonstração Interestadual (CFOP 6912)", is_same_uf=False, cfop="6912", effective_from=date(2020, 1, 1), priority=10, is_active=True
    )
    op_rem_demo.rules.extend([rule_rem_demo_int, rule_rem_demo_ext])

    # Transferência entre Filiais
    op_transf = FiscalOperation(
        id=uuid.uuid4(), tenant_id=tenant_id, company_id=company_id,
        code="TRANSFERENCIA", name="Transferência entre Filiais / Estabelecimentos",
        operation_type="OUT", purpose=1, affect_inventory=True, affect_financial=False,
        allowed_doc_models="55", description="Transferência de estoque entre unidades da mesma empresa.", is_active=True
    )
    rule_transf_int = FiscalScenarioRule(
        id=uuid.uuid4(), tenant_id=tenant_id, company_id=company_id, fiscal_operation_id=op_transf.id,
        description="Transferência Interna (CFOP 5152)", is_same_uf=True, cfop="5152", effective_from=date(2020, 1, 1), priority=10, is_active=True
    )
    rule_transf_ext = FiscalScenarioRule(
        id=uuid.uuid4(), tenant_id=tenant_id, company_id=company_id, fiscal_operation_id=op_transf.id,
        description="Transferência Interestadual (CFOP 6152)", is_same_uf=False, cfop="6152", effective_from=date(2020, 1, 1), priority=10, is_active=True
    )
    op_transf.rules.extend([rule_transf_int, rule_transf_ext])

    # Bonificação, Doação ou Brinde
    op_bonif = FiscalOperation(
        id=uuid.uuid4(), tenant_id=tenant_id, company_id=company_id,
        code="BONIFICACAO", name="Bonificação, Doação ou Brinde",
        operation_type="OUT", purpose=1, affect_inventory=True, affect_financial=False,
        allowed_doc_models="55", description="Remessa a título de bonificação, brinde ou doação.", is_active=True
    )
    rule_bonif_int = FiscalScenarioRule(
        id=uuid.uuid4(), tenant_id=tenant_id, company_id=company_id, fiscal_operation_id=op_bonif.id,
        description="Bonificação Interna (CFOP 5910)", is_same_uf=True, cfop="5910", effective_from=date(2020, 1, 1), priority=10, is_active=True
    )
    rule_bonif_ext = FiscalScenarioRule(
        id=uuid.uuid4(), tenant_id=tenant_id, company_id=company_id, fiscal_operation_id=op_bonif.id,
        description="Bonificação Interestadual (CFOP 6910)", is_same_uf=False, cfop="6910", effective_from=date(2020, 1, 1), priority=10, is_active=True
    )
    op_bonif.rules.extend([rule_bonif_int, rule_bonif_ext])

    # NF-e Complementar (finNFe 2)
    op_comp = FiscalOperation(
        id=uuid.uuid4(), tenant_id=tenant_id, company_id=company_id,
        code="NFE_COMPLEMENTAR", name="NF-e Complementar de Valor, Preço ou Imposto",
        operation_type="OUT", purpose=2, affect_inventory=False, affect_financial=False,
        allowed_doc_models="55", description="NF-e complementar de valor, quantidade ou imposto omitido/incorreto na nota original.", is_active=True
    )
    rule_comp_int = FiscalScenarioRule(
        id=uuid.uuid4(), tenant_id=tenant_id, company_id=company_id, fiscal_operation_id=op_comp.id,
        description="Complementar Interna (CFOP 5949)", is_same_uf=True, cfop="5949", effective_from=date(2020, 1, 1), priority=10, is_active=True
    )
    rule_comp_ext = FiscalScenarioRule(
        id=uuid.uuid4(), tenant_id=tenant_id, company_id=company_id, fiscal_operation_id=op_comp.id,
        description="Complementar Interestadual (CFOP 6949)", is_same_uf=False, cfop="6949", effective_from=date(2020, 1, 1), priority=10, is_active=True
    )
    op_comp.rules.extend([rule_comp_int, rule_comp_ext])

    # NF-e de Ajuste (finNFe 3)
    op_ajuste = FiscalOperation(
        id=uuid.uuid4(), tenant_id=tenant_id, company_id=company_id,
        code="NFE_AJUSTE", name="NF-e de Ajuste Fiscal ou Contábil",
        operation_type="OUT", purpose=3, affect_inventory=False, affect_financial=False,
        allowed_doc_models="55", description="NF-e destinada a ajustes fiscais ou escriturais previstos na legislação.", is_active=True
    )
    rule_ajuste_int = FiscalScenarioRule(
        id=uuid.uuid4(), tenant_id=tenant_id, company_id=company_id, fiscal_operation_id=op_ajuste.id,
        description="Ajuste Interno (CFOP 5949)", is_same_uf=True, cfop="5949", effective_from=date(2020, 1, 1), priority=10, is_active=True
    )
    rule_ajuste_ext = FiscalScenarioRule(
        id=uuid.uuid4(), tenant_id=tenant_id, company_id=company_id, fiscal_operation_id=op_ajuste.id,
        description="Ajuste Interestadual (CFOP 6949)", is_same_uf=False, cfop="6949", effective_from=date(2020, 1, 1), priority=10, is_active=True
    )
    op_ajuste.rules.extend([rule_ajuste_int, rule_ajuste_ext])

    all_ops = [
        op_venda_int, op_venda_ext, op_devolucao, op_dev_venda,
        op_rem_conserto, op_rem_demo, op_transf, op_bonif,
        op_comp, op_ajuste
    ]
    db.add_all(all_ops)
    db.commit()
    for o in all_ops:
        db.refresh(o)

    return all_ops


def create_fiscal_operation(
    db: Session,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    payload: FiscalOperationCreate,
) -> FiscalOperation:
    op = FiscalOperation(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=company_id,
        code=payload.code.upper().strip(),
        name=payload.name,
        operation_type=payload.operation_type.upper(),
        purpose=payload.purpose,
        affect_inventory=payload.affect_inventory,
        affect_financial=payload.affect_financial,
        allowed_doc_models=payload.allowed_doc_models,
        description=payload.description,
        is_active=payload.is_active,
    )

    if payload.rules:
        for r_payload in payload.rules:
            rule = FiscalScenarioRule(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                company_id=company_id,
                fiscal_operation_id=op.id,
                description=r_payload.description,
                uf_origin=r_payload.uf_origin.upper() if r_payload.uf_origin else None,
                uf_destination=r_payload.uf_destination.upper() if r_payload.uf_destination else None,
                is_same_uf=r_payload.is_same_uf,
                is_final_consumer=r_payload.is_final_consumer,
                is_tax_contributor=r_payload.is_tax_contributor,
                cfop=r_payload.cfop,
                cst_csosn_override=r_payload.cst_csosn_override,
                icms_aliquot_override=r_payload.icms_aliquot_override,
                fcp_aliquot_override=r_payload.fcp_aliquot_override,
                effective_from=r_payload.effective_from,
                effective_to=r_payload.effective_to,
                priority=r_payload.priority,
                is_active=r_payload.is_active,
            )
            op.rules.append(rule)

    db.add(op)
    db.commit()
    db.refresh(op)
    return op


def update_fiscal_operation(
    db: Session,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    op_id: uuid.UUID,
    payload: FiscalOperationUpdate,
) -> FiscalOperation:
    op = db.scalar(
        select(FiscalOperation).where(
            FiscalOperation.id == op_id,
            FiscalOperation.company_id == company_id,
            FiscalOperation.tenant_id == tenant_id,
        )
    )
    if not op:
        raise ValueError("Operação fiscal não encontrada.")

    for field, val in payload.model_dump(exclude_unset=True).items():
        if field == "code" and val:
            setattr(op, field, val.upper().strip())
        elif field == "operation_type" and val:
            setattr(op, field, val.upper())
        else:
            setattr(op, field, val)

    db.commit()
    db.refresh(op)
    return op


def add_scenario_rule(
    db: Session,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    op_id: uuid.UUID,
    payload: FiscalScenarioRuleCreate,
) -> FiscalScenarioRule:
    op = db.scalar(
        select(FiscalOperation).where(
            FiscalOperation.id == op_id,
            FiscalOperation.company_id == company_id,
            FiscalOperation.tenant_id == tenant_id,
        )
    )
    if not op:
        raise ValueError("Operação fiscal pai não encontrada.")

    rule = FiscalScenarioRule(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=company_id,
        fiscal_operation_id=op_id,
        description=payload.description,
        uf_origin=payload.uf_origin.upper() if payload.uf_origin else None,
        uf_destination=payload.uf_destination.upper() if payload.uf_destination else None,
        is_same_uf=payload.is_same_uf,
        is_final_consumer=payload.is_final_consumer,
        is_tax_contributor=payload.is_tax_contributor,
        cfop=payload.cfop,
        cst_csosn_override=payload.cst_csosn_override,
        icms_aliquot_override=payload.icms_aliquot_override,
        fcp_aliquot_override=payload.fcp_aliquot_override,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        priority=payload.priority,
        is_active=payload.is_active,
    )

    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def update_scenario_rule(
    db: Session,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    rule_id: uuid.UUID,
    payload: FiscalScenarioRuleUpdate,
) -> FiscalScenarioRule:
    rule = db.scalar(
        select(FiscalScenarioRule).where(
            FiscalScenarioRule.id == rule_id,
            FiscalScenarioRule.company_id == company_id,
            FiscalScenarioRule.tenant_id == tenant_id,
        )
    )
    if not rule:
        raise ValueError("Regra de cenário fiscal não encontrada.")

    for field, val in payload.model_dump(exclude_unset=True).items():
        if field in ["uf_origin", "uf_destination"] and val:
            setattr(rule, field, val.upper())
        else:
            setattr(rule, field, val)

    db.commit()
    db.refresh(rule)
    return rule


def delete_scenario_rule(
    db: Session, tenant_id: uuid.UUID, company_id: uuid.UUID, rule_id: uuid.UUID
):
    rule = db.scalar(
        select(FiscalScenarioRule).where(
            FiscalScenarioRule.id == rule_id,
            FiscalScenarioRule.company_id == company_id,
            FiscalScenarioRule.tenant_id == tenant_id,
        )
    )
    if not rule:
        raise ValueError("Regra de cenário fiscal não encontrada.")

    db.delete(rule)
    db.commit()


def resolve_fiscal_scenario(
    db: Session,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    req: FiscalScenarioMatchRequest,
) -> FiscalScenarioMatchResult:
    """
    Motor de Resolução de Cenário Fiscal:
    Busca a operação e regra vigente com maior especificidade e menor número de prioridade.
    """
    op_query = select(FiscalOperation).where(
        FiscalOperation.company_id == company_id,
        FiscalOperation.tenant_id == tenant_id,
        FiscalOperation.is_active == True,
    )

    if req.operation_code:
        op_query = op_query.where(FiscalOperation.code == req.operation_code.upper().strip())
    else:
        op_query = op_query.where(FiscalOperation.operation_type == req.operation_type.upper())

    ops = list(db.scalars(op_query).all())

    # Filtrar apenas operações que permitem o modelo de documento
    matching_ops = []
    for op in ops:
        models = [m.strip() for m in op.allowed_doc_models.split(",")]
        if req.doc_model in models:
            matching_ops.append(op)

    if not matching_ops:
        return FiscalScenarioMatchResult(
            matched=False,
            reason=f"Nenhuma operação fiscal ativa encontrada para o modelo {req.doc_model} e código {req.operation_code or req.operation_type}.",
        )

    is_same_uf = req.uf_origin.upper() == req.uf_destination.upper()
    op_date = req.operation_date or date.today()

    best_rule: Optional[FiscalScenarioRule] = None
    best_op: Optional[FiscalOperation] = None
    best_score: int = -1

    for op in matching_ops:
        for rule in op.rules:
            if not rule.is_active:
                continue

            # Checar vigência de data
            if rule.effective_from > op_date:
                continue
            if rule.effective_to and rule.effective_to < op_date:
                continue

            # Checar filtros de UF
            if rule.uf_origin and rule.uf_origin.upper() != req.uf_origin.upper():
                continue
            if rule.uf_destination and rule.uf_destination.upper() != req.uf_destination.upper():
                continue
            if rule.is_same_uf is not None and rule.is_same_uf != is_same_uf:
                continue

            # Checar filtros de consumidor final e contribuinte
            if rule.is_final_consumer is not None and rule.is_final_consumer != req.is_final_consumer:
                continue
            if rule.is_tax_contributor is not None and rule.is_tax_contributor != req.is_tax_contributor:
                continue

            # Calcular pontuação de especificidade
            score = 0
            if rule.uf_origin:
                score += 10
            if rule.uf_destination:
                score += 10
            if rule.is_same_uf is not None:
                score += 5
            if rule.is_final_consumer is not None:
                score += 5
            if rule.is_tax_contributor is not None:
                score += 5

            # Menor priority = valor numérico menor ganha peso extra na pontuação
            score += (100 - rule.priority)

            if score > best_score:
                best_score = score
                best_rule = rule
                best_op = op

    if not best_rule or not best_op:
        return FiscalScenarioMatchResult(
            matched=False,
            reason="Nenhuma regra de cenário fiscal vigente atendeu aos critérios de UF, Consumidor Final ou Contribuinte.",
        )

    return FiscalScenarioMatchResult(
        matched=True,
        fiscal_operation_id=best_op.id,
        operation_name=best_op.name,
        purpose=best_op.purpose,
        affect_inventory=best_op.affect_inventory,
        affect_financial=best_op.affect_financial,
        rule_id=best_rule.id,
        rule_description=best_rule.description,
        cfop=best_rule.cfop,
        cst_csosn_override=best_rule.cst_csosn_override,
        icms_aliquot_override=float(best_rule.icms_aliquot_override) if best_rule.icms_aliquot_override is not None else None,
        fcp_aliquot_override=float(best_rule.fcp_aliquot_override) if best_rule.fcp_aliquot_override is not None else None,
        reason=f"Regra '{best_rule.description}' casada com sucesso com CFOP {best_rule.cfop}.",
    )
