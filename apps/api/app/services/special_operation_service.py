import uuid
import re
import json
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.company import Company
from app.models.company_fiscal import FiscalCompanyConfig, FiscalCertificate
from app.models.product import Product
from app.models.product_fiscal import ProductFiscalProfile
from app.models.fiscal_operation import FiscalOperation
from app.models.nfe_document import NfeDocument, NfeItem, NfeStatus
from app.models.stock import StockMovement, StockMovementType
from app.models.audit import AuditLog
from app.schemas.special_operation import SpecialOperationCreateRequest, ComplementaryAdjustmentCreateRequest
from app.schemas.fiscal_operation import FiscalScenarioMatchRequest
from app.schemas.tax_engine import (
    TaxCalculationInput,
    ProductTaxProfileInput,
    OperationResolvedInput,
    RecipientInput,
    ItemFinancialContextInput,
)
from app.services.nfe_xml_builder import generate_access_key, NfeXmlBuilder
from app.services.nfe_signer import NfeSigner
from app.services.fiscal_operation import resolve_fiscal_scenario
from app.services.tax_engine import TaxEngine
from app.core.crypto import decrypt_data, decrypt_text


def create_special_operation_nfe(
    db: Session,
    tenant_id: uuid.UUID,
    payload: SpecialOperationCreateRequest,
    user_id: Optional[uuid.UUID] = None,
) -> NfeDocument:
    """
    Cria e processa rascunho de NF-e para Operações Especiais (Devolução, Remessa, Transferência, Bonificação).
    Valida obrigatoriedade de Chave Referenciada (44 dígitos) em Devoluções e aplica separação estrita de Estoque/Financeiro.
    """
    company = db.scalar(
        select(Company).where(Company.id == payload.company_id, Company.tenant_id == tenant_id)
    )
    if not company:
        raise ValueError("Empresa emissora não encontrada.")

    fiscal_config = db.scalar(
        select(FiscalCompanyConfig).where(
            FiscalCompanyConfig.company_id == payload.company_id,
            FiscalCompanyConfig.tenant_id == tenant_id,
        )
    )
    crt = fiscal_config.crt if fiscal_config else 1
    company_uf = "SP"

    # Resolve a Operação Fiscal por código
    operation = db.scalar(
        select(FiscalOperation).where(
            FiscalOperation.company_id == payload.company_id,
            FiscalOperation.tenant_id == tenant_id,
            FiscalOperation.code == payload.operation_code.upper().strip(),
        )
    )
    if not operation:
        raise ValueError(f"Operação fiscal '{payload.operation_code}' não encontrada ou não cadastrada para a empresa.")

    # Validação de Chave Referenciada para Devolução (finNFe == 4)
    clean_ref_key = None
    if operation.purpose == 4:
        if not payload.referenced_nfe_key:
            raise ValueError("Chave de Acesso da NF-e original é obrigatória para operações de Devolução/Retorno (finNFe 4).")
        clean_ref_key = re.sub(r"\D", "", payload.referenced_nfe_key)
        if len(clean_ref_key) != 44:
            raise ValueError(f"Chave de Acesso referenciada inválida ({len(clean_ref_key)} dígitos). Deve possuir exatamente 44 dígitos numéricos.")
    elif payload.referenced_nfe_key:
        clean_ref_key = re.sub(r"\D", "", payload.referenced_nfe_key)

    # Próximo número da série
    next_number = 1
    max_num = db.scalar(
        select(NfeDocument.number).where(
            NfeDocument.company_id == payload.company_id,
            NfeDocument.tenant_id == tenant_id,
            NfeDocument.model == "55",
        ).order_by(NfeDocument.number.desc())
    )
    if max_num:
        next_number = max_num + 1

    access_key = generate_access_key(
        uf=company_uf,
        issue_date=datetime.now(timezone.utc),
        cnpj=company.cnpj,
        model=55,
        series=1,
        number=next_number,
    )

    doc = NfeDocument(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=payload.company_id,
        fiscal_operation_id=operation.id,
        access_key=access_key,
        number=next_number,
        series=1,
        model="55",
        nature_of_operation=operation.name,
        operation_type_nfe=0 if operation.operation_type == "IN" else 1,
        purpose=operation.purpose,
        issue_type=1,
        environment=fiscal_config.environment if fiscal_config else 2,
        status=NfeStatus.DRAFT.value,

        issuer_cnpj=company.cnpj,
        issuer_name=company.name,
        issuer_trade_name=company.trade_name,
        issuer_ie=company.state_registration,
        issuer_crt=crt,
        issuer_uf=company_uf,

        recipient_cnpj_cpf=re.sub(r"\D", "", payload.recipient_cnpj_cpf),
        recipient_name=payload.recipient_name,
        recipient_uf=payload.recipient_uf.upper(),
        recipient_is_final_consumer=payload.recipient_is_final_consumer,
        recipient_is_tax_contributor=payload.recipient_is_tax_contributor,

        referenced_nfe_key=clean_ref_key,
    )

    # Processar Itens & Cálculos Fiscais
    items_list = []
    tot_vProd = 0.0
    tot_vBC = 0.0
    tot_vICMS = 0.0

    for idx, item_input in enumerate(payload.items, start=1):
        product = db.scalar(
            select(Product).where(
                Product.id == item_input.product_id,
                Product.company_id == payload.company_id,
            )
        )
        if not product:
            raise ValueError(f"Produto com ID {item_input.product_id} não encontrado.")

        profile = db.scalar(
            select(ProductFiscalProfile).where(
                ProductFiscalProfile.product_id == product.id,
                ProductFiscalProfile.company_id == payload.company_id,
            )
        )

        scenario = resolve_fiscal_scenario(
            db=db,
            tenant_id=tenant_id,
            company_id=payload.company_id,
            req=FiscalScenarioMatchRequest(
                operation_code=operation.code,
                operation_type=operation.operation_type,
                uf_origin=doc.issuer_uf,
                uf_destination=doc.recipient_uf,
                is_final_consumer=doc.recipient_is_final_consumer,
                is_tax_contributor=doc.recipient_is_tax_contributor,
                doc_model="55",
            ),
        )
        cfop = scenario.cfop if scenario else ("5102" if doc.issuer_uf == doc.recipient_uf else "6102")

        item_total = round(item_input.quantity * item_input.unit_price, 2)
        tot_vProd += item_total

        tax_input = TaxCalculationInput(
            company_crt=crt,
            company_uf=company_uf,
            product=ProductTaxProfileInput(
                ncm=product.ncm or "20091200",
                origem=str(profile.origin) if profile else "0",
                cst_csosn=scenario.cst_csosn_override if (scenario and scenario.cst_csosn_override) else ("102" if crt == 1 else "00"),
            ),
            operation=OperationResolvedInput(
                operation_code=operation.code,
                operation_name=operation.name,
                cfop=cfop,
                cst_csosn_override=scenario.cst_csosn_override if scenario else None,
                icms_aliquot_override=scenario.icms_aliquot_override if scenario else None,
            ),
            recipient=RecipientInput(
                uf=doc.recipient_uf,
                is_final_consumer=doc.recipient_is_final_consumer,
                is_tax_contributor=doc.recipient_is_tax_contributor,
            ),
            context=ItemFinancialContextInput(
                vProd=item_total,
                qCom=item_input.quantity,
                vUnCom=item_input.unit_price,
            ),
        )
        tax_snap = TaxEngine.calculate_item_tax(tax_input)

        tot_vBC += tax_snap.icms.vBC_ICMS
        tot_vICMS += tax_snap.icms.vICMS

        n_item = NfeItem(
            id=uuid.uuid4(),
            nfe_id=doc.id,
            product_id=product.id,
            item_number=idx,
            product_code=product.code or f"PROD-{idx}",
            gtin="SEM GTIN",
            description=product.name,
            ncm=product.ncm or "20091200",
            cfop=cfop,
            uCom="UN",
            qCom=item_input.quantity,
            vUnCom=item_input.unit_price,
            vProd=item_total,
            uTrib="UN",
            qTrib=item_input.quantity,
            vUnTrib=item_input.unit_price,
            tax_snapshot_json=tax_snap.model_dump(),
        )
        items_list.append(n_item)

        # Movimentação de Estoque se affect_inventory == True
        if operation.affect_inventory:
            prev_qty = float(product.stock_qty or 0.0)
            if operation.operation_type == "IN":
                new_qty = prev_qty + item_input.quantity
                mov_type = StockMovementType.ENTRADA_NF
            else:
                new_qty = max(0.0, prev_qty - item_input.quantity)
                mov_type = StockMovementType.SAIDA_VENDA

            product.stock_qty = new_qty
            db.add(product)

            stock_mov = StockMovement(
                tenant_id=tenant_id,
                company_id=payload.company_id,
                product_id=product.id,
                user_id=user_id or uuid.uuid4(),
                movement_type=mov_type,
                quantity=item_input.quantity,
                previous_qty=prev_qty,
                new_qty=new_qty,
                unit_cost=float(product.cost or 0.0),
                reference_doc=f"NF-e {doc.number} ({operation.code})",
                notes=f"Movimentação por Operação Especial: {operation.name}",
            )
            db.add(stock_mov)

    doc.vProd = tot_vProd
    doc.vBC = tot_vBC
    doc.vICMS = tot_vICMS
    doc.vNF = tot_vProd
    doc.items = items_list

    # Geração do XML e Assinatura A1
    raw_xml = NfeXmlBuilder.build_nfe_xml(doc)
    doc.raw_xml = raw_xml

    cert = db.scalar(
        select(FiscalCertificate).where(
            FiscalCertificate.company_id == payload.company_id,
            FiscalCertificate.tenant_id == tenant_id,
            FiscalCertificate.is_active == True,
        )
    )
    if cert:
        pfx_bytes = decrypt_data(cert.certificate_data_encrypted)
        password = decrypt_text(cert.password_encrypted)
        doc.signed_xml = NfeSigner.sign_nfe_xml(raw_xml, pfx_bytes, password)
        doc.status = NfeStatus.SIGNED.value

    db.add(doc)

    if user_id:
        audit = AuditLog(
            tenant_id=tenant_id,
            company_id=payload.company_id,
            user_id=user_id,
            action="SPECIAL_OPERATION_NFE_CREATED",
            entity="nfe_document",
            entity_id=doc.id,
            after_data=json.dumps({
                "operation_code": operation.code,
                "access_key": doc.access_key,
                "referenced_nfe_key": clean_ref_key,
                "affect_inventory": operation.affect_inventory,
                "affect_financial": operation.affect_financial,
                "total_vNF": float(doc.vNF),
            }),
        )
        db.add(audit)

    db.commit()
    db.refresh(doc)
    return doc


def create_complementary_adjustment_nfe(
    db: Session,
    tenant_id: uuid.UUID,
    payload: ComplementaryAdjustmentCreateRequest,
    user_id: Optional[uuid.UUID] = None,
) -> NfeDocument:
    """
    Cria e processa rascunho de NF-e Complementar (finNFe 2) ou de Ajuste (finNFe 3).
    Valida obrigatoriamente:
    1. finalidade (purpose): 2 (Complementar) ou 3 (Ajuste).
    2. chave referenciada (referenced_nfe_key): exatamente 44 dígitos numéricos.
    3. motivo (reason): não nulo / min_length >= 10.
    4. preservação da nota original: se a nota referenciada existir no banco, seu status permanece inalterado (NÃO SUBSTITUI A NOTA ORIGINAL).
    5. inclusão das informações adicionais (<infAdic><infCpl>) no XML.
    """
    if payload.purpose not in [2, 3]:
        raise ValueError("Finalidade inválida para NF-e Complementar/Ajuste. Deve ser 2 (Complementar) ou 3 (Ajuste).")

    if not payload.referenced_nfe_key:
        raise ValueError("Chave de Acesso da NF-e original é obrigatória para NF-e Complementar ou de Ajuste.")
    clean_ref_key = re.sub(r"\D", "", payload.referenced_nfe_key)
    if len(clean_ref_key) != 44:
        raise ValueError(f"Chave de Acesso referenciada inválida ({len(clean_ref_key)} dígitos). Deve possuir exatamente 44 dígitos numéricos.")

    clean_reason = (payload.reason or "").strip()
    if len(clean_reason) < 10:
        raise ValueError("O motivo da emissão complementar ou de ajuste é obrigatório e deve conter no mínimo 10 caracteres.")

    # Verificação da Nota Original no Banco (Garantir NÃO SUBSTITUIÇÃO)
    original_doc = db.scalar(
        select(NfeDocument).where(NfeDocument.access_key == clean_ref_key)
    )
    # original_doc permanece totalmente intocado.

    company = db.scalar(
        select(Company).where(Company.id == payload.company_id, Company.tenant_id == tenant_id)
    )
    if not company:
        raise ValueError("Empresa emissora não encontrada.")

    fiscal_config = db.scalar(
        select(FiscalCompanyConfig).where(
            FiscalCompanyConfig.company_id == payload.company_id,
            FiscalCompanyConfig.tenant_id == tenant_id,
        )
    )
    crt = fiscal_config.crt if fiscal_config else 1
    company_uf = "SP"

    default_op_code = "NFE_COMPLEMENTAR" if payload.purpose == 2 else "NFE_AJUSTE"
    op_code = (payload.operation_code or default_op_code).upper().strip()

    operation = db.scalar(
        select(FiscalOperation).where(
            FiscalOperation.company_id == payload.company_id,
            FiscalOperation.tenant_id == tenant_id,
            FiscalOperation.code == op_code,
        )
    )
    if not operation:
        operation = db.scalar(
            select(FiscalOperation).where(
                FiscalOperation.company_id == payload.company_id,
                FiscalOperation.tenant_id == tenant_id,
                FiscalOperation.code == default_op_code,
            )
        )
    if not operation:
        raise ValueError(f"Operação fiscal '{op_code}' não encontrada para a empresa.")

    finality_label = "COMPLEMENTAR" if payload.purpose == 2 else "AJUSTE"
    inf_cpl_text = f"NF-E {finality_label} REFERENTE A NF-E CHAVE {clean_ref_key}. MOTIVO: {clean_reason}"
    if payload.notes:
        inf_cpl_text += f" | OBS: {payload.notes.strip()}"

    next_number = 1
    max_num = db.scalar(
        select(NfeDocument.number).where(
            NfeDocument.company_id == payload.company_id,
            NfeDocument.tenant_id == tenant_id,
            NfeDocument.model == "55",
        ).order_by(NfeDocument.number.desc())
    )
    if max_num:
        next_number = max_num + 1

    access_key = generate_access_key(
        uf=company_uf,
        issue_date=datetime.now(timezone.utc),
        cnpj=company.cnpj,
        model=55,
        series=1,
        number=next_number,
    )

    doc = NfeDocument(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=payload.company_id,
        fiscal_operation_id=operation.id,
        access_key=access_key,
        number=next_number,
        series=1,
        model="55",
        nature_of_operation=operation.name,
        operation_type_nfe=0 if operation.operation_type == "IN" else 1,
        purpose=payload.purpose,
        issue_type=1,
        environment=fiscal_config.environment if fiscal_config else 2,
        status=NfeStatus.DRAFT.value,

        issuer_cnpj=company.cnpj,
        issuer_name=company.name,
        issuer_trade_name=company.trade_name,
        issuer_ie=company.state_registration,
        issuer_crt=crt,
        issuer_uf=company_uf,

        recipient_cnpj_cpf=re.sub(r"\D", "", payload.recipient_cnpj_cpf),
        recipient_name=payload.recipient_name,
        recipient_uf=payload.recipient_uf.upper(),
        recipient_is_final_consumer=payload.recipient_is_final_consumer,
        recipient_is_tax_contributor=payload.recipient_is_tax_contributor,

        referenced_nfe_key=clean_ref_key,
        additional_information=inf_cpl_text,
    )

    items_list = []
    tot_vProd = 0.0
    tot_vBC = 0.0
    tot_vICMS = 0.0

    for idx, item_input in enumerate(payload.items, start=1):
        product = db.scalar(
            select(Product).where(
                Product.id == item_input.product_id,
                Product.company_id == payload.company_id,
            )
        )
        if not product:
            raise ValueError(f"Produto com ID {item_input.product_id} não encontrado.")

        profile = db.scalar(
            select(ProductFiscalProfile).where(
                ProductFiscalProfile.product_id == product.id,
                ProductFiscalProfile.company_id == payload.company_id,
            )
        )

        scenario = resolve_fiscal_scenario(
            db=db,
            tenant_id=tenant_id,
            company_id=payload.company_id,
            req=FiscalScenarioMatchRequest(
                operation_code=operation.code,
                operation_type=operation.operation_type,
                uf_origin=doc.issuer_uf,
                uf_destination=doc.recipient_uf,
                is_final_consumer=doc.recipient_is_final_consumer,
                is_tax_contributor=doc.recipient_is_tax_contributor,
                doc_model="55",
            ),
        )
        cfop = scenario.cfop if scenario else ("5949" if doc.issuer_uf == doc.recipient_uf else "6949")

        item_total = round(item_input.quantity * item_input.unit_price, 2)
        tot_vProd += item_total

        tax_input = TaxCalculationInput(
            company_crt=crt,
            company_uf=company_uf,
            product=ProductTaxProfileInput(
                ncm=product.ncm or "20091200",
                origem=str(profile.origin) if profile else "0",
                cst_csosn=scenario.cst_csosn_override if (scenario and scenario.cst_csosn_override) else ("102" if crt == 1 else "00"),
            ),
            operation=OperationResolvedInput(
                operation_code=operation.code,
                operation_name=operation.name,
                cfop=cfop,
                cst_csosn_override=scenario.cst_csosn_override if scenario else None,
                icms_aliquot_override=scenario.icms_aliquot_override if scenario else None,
            ),
            recipient=RecipientInput(
                uf=doc.recipient_uf,
                is_final_consumer=doc.recipient_is_final_consumer,
                is_tax_contributor=doc.recipient_is_tax_contributor,
            ),
            context=ItemFinancialContextInput(
                vProd=item_total,
                qCom=item_input.quantity,
                vUnCom=item_input.unit_price,
            ),
        )
        tax_snap = TaxEngine.calculate_item_tax(tax_input)

        tot_vBC += tax_snap.icms.vBC_ICMS
        tot_vICMS += tax_snap.icms.vICMS

        n_item = NfeItem(
            id=uuid.uuid4(),
            nfe_id=doc.id,
            product_id=product.id,
            item_number=idx,
            product_code=product.code or f"PROD-{idx}",
            gtin="SEM GTIN",
            description=product.name,
            ncm=product.ncm or "20091200",
            cfop=cfop,
            uCom="UN",
            qCom=item_input.quantity,
            vUnCom=item_input.unit_price,
            vProd=item_total,
            uTrib="UN",
            qTrib=item_input.quantity,
            vUnTrib=item_input.unit_price,
            tax_snapshot_json=tax_snap.model_dump(),
        )
        items_list.append(n_item)

        if payload.affect_inventory:
            prev_qty = float(product.stock_qty or 0.0)
            if operation.operation_type == "IN":
                new_qty = prev_qty + item_input.quantity
                mov_type = StockMovementType.ENTRADA_NF
            else:
                new_qty = max(0.0, prev_qty - item_input.quantity)
                mov_type = StockMovementType.SAIDA_VENDA

            product.stock_qty = new_qty
            db.add(product)

            stock_mov = StockMovement(
                tenant_id=tenant_id,
                company_id=payload.company_id,
                product_id=product.id,
                user_id=user_id or uuid.uuid4(),
                movement_type=mov_type,
                quantity=item_input.quantity,
                previous_qty=prev_qty,
                new_qty=new_qty,
                unit_cost=float(product.cost or 0.0),
                reference_doc=f"NF-e {doc.number} ({finality_label})",
                notes=f"Movimentação por NF-e {finality_label}: {clean_reason}",
            )
            db.add(stock_mov)

    doc.vProd = tot_vProd
    doc.vBC = tot_vBC
    doc.vICMS = tot_vICMS
    doc.vNF = tot_vProd
    doc.items = items_list

    raw_xml = NfeXmlBuilder.build_nfe_xml(doc)
    doc.raw_xml = raw_xml

    cert = db.scalar(
        select(FiscalCertificate).where(
            FiscalCertificate.company_id == payload.company_id,
            FiscalCertificate.tenant_id == tenant_id,
            FiscalCertificate.is_active == True,
        )
    )
    if cert:
        pfx_bytes = decrypt_data(cert.certificate_data_encrypted)
        password = decrypt_text(cert.password_encrypted)
        doc.signed_xml = NfeSigner.sign_nfe_xml(raw_xml, pfx_bytes, password)
        doc.status = NfeStatus.SIGNED.value

    db.add(doc)

    if user_id:
        audit = AuditLog(
            tenant_id=tenant_id,
            company_id=payload.company_id,
            user_id=user_id,
            action=f"COMPLEMENTARY_ADJUSTMENT_NFE_CREATED_{finality_label}",
            entity="nfe_document",
            entity_id=doc.id,
            after_data=json.dumps({
                "purpose": payload.purpose,
                "access_key": doc.access_key,
                "referenced_nfe_key": clean_ref_key,
                "reason": clean_reason,
                "total_vNF": float(doc.vNF),
            }),
        )
        db.add(audit)

    db.commit()
    db.refresh(doc)
    return doc

