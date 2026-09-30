import uuid
import base64
import hashlib
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.company import Company
from app.models.company_fiscal import FiscalCompanyConfig, FiscalSeries, FiscalCertificate
from app.models.fiscal_operation import FiscalOperation
from app.models.nfe_document import NfeDocument, NfeItem, NfeStatus
from app.schemas.nfe import NfeDocumentCreate
from app.schemas.tax_engine import (
    TaxCalculationInput,
    ProductTaxProfileInput,
    RecipientInput,
    OperationResolvedInput,
    ItemFinancialContextInput,
)
from app.services.tax_engine import TaxEngine
from app.services.company_fiscal import increment_fiscal_series_number
from app.services.fiscal_operation import resolve_fiscal_scenario
from app.services.nfe_xml_builder import generate_access_key, NfeXmlBuilder
from app.services.nfe_signer import NfeSigner
from app.core.crypto import decrypt_data, decrypt_text


def create_nfe_draft(
    db: Session,
    tenant_id: uuid.UUID,
    payload: NfeDocumentCreate,
) -> NfeDocument:
    """
    Cria o rascunho (DRAFT) da NF-e Modelo 55, executando o TaxEngine para cada item
    e gerando a Chave de Acesso SEFAZ de 44 dígitos.
    """
    # 1. Carregar dados da empresa emitente
    company = db.scalar(
        select(Company).where(Company.id == payload.company_id, Company.tenant_id == tenant_id)
    )
    if not company:
        raise ValueError("Empresa emitente não encontrada.")

    fiscal_config = db.scalar(
        select(FiscalCompanyConfig).where(
            FiscalCompanyConfig.company_id == payload.company_id,
            FiscalCompanyConfig.tenant_id == tenant_id,
        )
    )
    crt = fiscal_config.crt if fiscal_config else 1
    company_uf = (getattr(company, "state", None) or "SP").upper()

    # 2. Obter numeração sequencial da série 1 (Modelo 55)
    doc_number = increment_fiscal_series_number(db, tenant_id, payload.company_id, doc_model="55", series=1)

    # 3. Gerar Chave de Acesso SEFAZ de 44 dígitos
    issue_date = datetime.now(timezone.utc)
    access_key = generate_access_key(
        uf=company_uf,
        issue_date=issue_date,
        cnpj=company.cnpj or "00000000000000",
        model=55,
        series=1,
        number=doc_number,
        issue_type=1
    )

    # 4. Resolver Operação Fiscal Padrão
    op_match = resolve_fiscal_scenario(
        db,
        tenant_id,
        payload.company_id,
        req=type("Req", (), {
            "operation_code": payload.fiscal_operation_code,
            "operation_type": "OUT",
            "uf_origin": company_uf,
            "uf_destination": payload.recipient_uf,
            "is_final_consumer": payload.recipient_is_final_consumer,
            "is_tax_contributor": payload.recipient_is_tax_contributor,
            "doc_model": "55",
            "operation_date": issue_date.date(),
        })()
    )

    if not op_match.matched:
        raise ValueError(f"Não foi possível resolver a operação fiscal: {op_match.reason}")

    doc = NfeDocument(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=payload.company_id,
        fiscal_operation_id=op_match.fiscal_operation_id,
        sale_id=payload.sale_id,
        purchase_id=payload.purchase_id,
        access_key=access_key,
        number=doc_number,
        series=1,
        model="55",
        nature_of_operation=op_match.operation_name or "Venda de Mercadoria",
        issue_type=1,
        environment=fiscal_config.environment if fiscal_config else 2,
        status=NfeStatus.DRAFT.value,
        
        # Snapshot Emitente
        issuer_cnpj=company.cnpj or "00000000000000",
        issuer_name=company.name,
        issuer_trade_name=company.trade_name,
        issuer_ie=company.state_registration,
        issuer_crt=crt,
        issuer_uf=company_uf,
        issuer_address={
            "xLgr": getattr(company, "street", None) or "Rua Principal",
            "nro": getattr(company, "number", None) or "100",
            "xBairro": getattr(company, "neighborhood", None) or "Centro",
            "cMun": getattr(company, "city_code", None) or "3550308",
            "xMun": getattr(company, "city", None) or "Sao Paulo",
            "UF": company_uf,
            "CEP": getattr(company, "postal_code", None) or "01001000",
        },

        # Snapshot Destinatário
        recipient_cnpj_cpf=payload.recipient_cnpj_cpf,
        recipient_name=payload.recipient_name,
        recipient_ie=payload.recipient_ie,
        recipient_email=payload.recipient_email,
        recipient_uf=payload.recipient_uf.upper(),
        recipient_is_final_consumer=payload.recipient_is_final_consumer,
        recipient_is_tax_contributor=payload.recipient_is_tax_contributor,
        recipient_address=payload.recipient_address,
        referenced_nfe_key=payload.referenced_nfe_key,
    )

    # 5. Processar Itens e Executar o TaxEngine
    tot_vProd = 0.0
    tot_vFrete = 0.0
    tot_vSeguro = 0.0
    tot_vDesc = 0.0
    tot_vOutro = 0.0
    tot_vBC = 0.0
    tot_vICMS = 0.0
    tot_vFCP = 0.0
    tot_vBCST = 0.0
    tot_vST = 0.0
    tot_vIPI = 0.0
    tot_vPIS = 0.0
    tot_vCOFINS = 0.0
    tot_vNF = 0.0

    for idx, item_in in enumerate(payload.items, start=1):
        tax_input = TaxCalculationInput(
            company_crt=crt,
            company_uf=company_uf,
            company_pCredSN=2.85 if crt == 1 else 0.0,
            product=ProductTaxProfileInput(
                ncm=item_in.ncm,
                cest=item_in.cest,
                origem="0",
                cst_csosn=op_match.cst_csosn_override or ("102" if crt == 1 else "00"),
                icms_aliquot=op_match.icms_aliquot_override or (18.0 if crt == 3 else None),
            ),
            operation=OperationResolvedInput(
                operation_code=payload.fiscal_operation_code,
                operation_name=op_match.operation_name or "Venda de Mercadoria",
                cfop=op_match.cfop or "5102",
            ),
            recipient=RecipientInput(
                uf=payload.recipient_uf.upper(),
                is_final_consumer=payload.recipient_is_final_consumer,
                is_tax_contributor=payload.recipient_is_tax_contributor,
            ),
            context=ItemFinancialContextInput(
                vProd=item_in.vProd,
                qCom=item_in.qCom,
                vUnCom=item_in.vUnCom,
                vFrete=item_in.vFrete,
                vSeguro=item_in.vSeguro,
                vDesc=item_in.vDesc,
                vOutro=item_in.vOutro,
            ),
        )

        tax_snap = TaxEngine.calculate_item_tax(tax_input)

        nfe_item = NfeItem(
            id=uuid.uuid4(),
            nfe_id=doc.id,
            item_number=idx,
            product_id=item_in.product_id,
            product_code=item_in.product_code,
            gtin=item_in.gtin,
            description=item_in.description,
            ncm=item_in.ncm,
            cest=item_in.cest,
            cfop=op_match.cfop or "5102",
            uCom=item_in.uCom,
            qCom=item_in.qCom,
            vUnCom=item_in.vUnCom,
            vProd=item_in.vProd,
            uTrib=item_in.uCom,
            qTrib=item_in.qCom,
            vUnTrib=item_in.vUnCom,
            vFrete=item_in.vFrete,
            vSeguro=item_in.vSeguro,
            vDesc=item_in.vDesc,
            vOutro=item_in.vOutro,
            tax_snapshot_json=tax_snap.model_dump(),
        )
        doc.items.append(nfe_item)

        # Acumular totais consolidados
        tot_vProd += item_in.vProd
        tot_vFrete += item_in.vFrete
        tot_vSeguro += item_in.vSeguro
        tot_vDesc += item_in.vDesc
        tot_vOutro += item_in.vOutro

        tot_vBC += tax_snap.icms.vBC_ICMS
        tot_vICMS += tax_snap.icms.vICMS
        tot_vFCP += tax_snap.fcp.vFCP
        tot_vBCST += tax_snap.st.vBC_ICMSST
        tot_vST += tax_snap.st.vICMSST
        tot_vIPI += tax_snap.ipi.vIPI
        tot_vPIS += tax_snap.pis.vPIS
        tot_vCOFINS += tax_snap.cofins.vCOFINS
        tot_vNF += tax_snap.vItemTotal

    doc.vProd = round(tot_vProd, 2)
    doc.vFrete = round(tot_vFrete, 2)
    doc.vSeguro = round(tot_vSeguro, 2)
    doc.vDesc = round(tot_vDesc, 2)
    doc.vOutro = round(tot_vOutro, 2)
    doc.vBC = round(tot_vBC, 2)
    doc.vICMS = round(tot_vICMS, 2)
    doc.vFCP = round(tot_vFCP, 2)
    doc.vBCST = round(tot_vBCST, 2)
    doc.vST = round(tot_vST, 2)
    doc.vIPI = round(tot_vIPI, 2)
    doc.vPIS = round(tot_vPIS, 2)
    doc.vCOFINS = round(tot_vCOFINS, 2)
    doc.vNF = round(tot_vNF, 2)

    # 6. Gerar XML Rascunho SEFAZ v4.00
    doc.raw_xml = NfeXmlBuilder.build_nfe_xml(doc)

    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def sign_nfe_document(
    db: Session,
    tenant_id: uuid.UUID,
    nfe_id: uuid.UUID,
) -> NfeDocument:
    """
    Assina digitalmente o XML da NF-e usando o Certificado A1 ativo da empresa e altera o status para SIGNED.
    """
    doc = db.scalar(
        select(NfeDocument).where(NfeDocument.id == nfe_id, NfeDocument.tenant_id == tenant_id)
    )
    if not doc:
        raise ValueError("Nota Fiscal Eletrônica não encontrada.")

    if doc.status not in [NfeStatus.DRAFT.value, NfeStatus.SIGNED.value]:
        raise ValueError(f"Não é possível assinar NF-e no status '{doc.status}'. Deve estar em 'DRAFT'.")

    # Obter Certificado A1 ativo da empresa
    cert = db.scalar(
        select(FiscalCertificate).where(
            FiscalCertificate.company_id == doc.company_id,
            FiscalCertificate.tenant_id == tenant_id,
            FiscalCertificate.is_active == True,
        )
    )
    if not cert:
        raise ValueError("Empresa não possui um Certificado Digital A1 ativo cadastrado.")

    pfx_bytes = decrypt_data(cert.certificate_data_encrypted)
    password = decrypt_text(cert.password_encrypted)

    # Executar a Assinatura Digital W3C sobre o XML
    signed_xml = NfeSigner.sign_nfe_xml(doc.raw_xml, pfx_bytes, password)

    doc.signed_xml = signed_xml
    doc.status = NfeStatus.SIGNED.value

    db.commit()
    db.refresh(doc)
    return doc


def attach_authorization_protocol(
    db: Session,
    tenant_id: uuid.UUID,
    nfe_id: uuid.UUID,
    protocol_number: str = "135260001234567",
    sefaz_status_code: int = 100,
    sefaz_reason: str = "Autorizado o uso da NF-e",
) -> NfeDocument:
    """
    Simula / Anexa o protocolo de autorização SEFAZ e gera o XML de distribuição <nfeProc>.
    Transiciona o status para AUTHORIZED.
    """
    doc = db.scalar(
        select(NfeDocument).where(NfeDocument.id == nfe_id, NfeDocument.tenant_id == tenant_id)
    )
    if not doc:
        raise ValueError("Nota Fiscal Eletrônica não encontrada.")

    xml_to_process = doc.signed_xml or doc.raw_xml
    if not xml_to_process:
        raise ValueError("Nota Fiscal não possui XML válido para protocolo.")

    # Calcular DigestValue da NFe
    digest_val = base64.b64encode(hashlib.sha1(xml_to_process.encode("utf-8")).digest()).decode("utf-8")

    dh_now = datetime.now(timezone.utc)
    proc_xml = NfeXmlBuilder.build_nfe_proc_xml(
        signed_nfe_xml=xml_to_process,
        protocol_number=protocol_number,
        digest_value=digest_val,
        status_code=sefaz_status_code,
        reason=sefaz_reason,
        dh_rec=dh_now
    )

    doc.proc_xml = proc_xml
    doc.protocol_number = protocol_number
    doc.digest_value = digest_val
    doc.sefaz_status_code = sefaz_status_code
    doc.sefaz_reason = sefaz_reason
    doc.authorized_at = dh_now
    doc.status = NfeStatus.AUTHORIZED.value if sefaz_status_code == 100 else NfeStatus.REJECTED.value

    db.commit()
    db.refresh(doc)
    return doc
