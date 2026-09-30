import uuid
import re
import json
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.company import Company
from app.models.company_fiscal import FiscalCertificate
from app.models.nfse_document import NfseDocument, NfseStatus
from app.models.audit import AuditLog
from app.schemas.nfse import NfseCreateRequest, NfseCancelRequest, NfseEmissionResult
from app.services.nfse_provider import NfseProviderFactory
from app.core.crypto import decrypt_data, decrypt_text


def create_and_emit_nfse(
    db: Session,
    tenant_id: uuid.UUID,
    payload: NfseCreateRequest,
    user_id: Optional[uuid.UUID] = None,
) -> NfseEmissionResult:
    """
    Cria rascunho de DPS e transmite NFS-e via NfseProviderFactory (Padrão Nacional SEFIN ou Adapter Municipal).
    Calcula ISSQN, retenções de impostos de serviço e grava protocolo e auditoria.
    """
    company = db.scalar(
        select(Company).where(Company.id == payload.company_id, Company.tenant_id == tenant_id)
    )
    if not company:
        raise ValueError("Empresa prestadora não encontrada.")

    # Obter certificado A1 ativo para assinatura da DPS
    cert = db.scalar(
        select(FiscalCertificate).where(
            FiscalCertificate.company_id == payload.company_id,
            FiscalCertificate.tenant_id == tenant_id,
            FiscalCertificate.is_active == True,
        )
    )
    if not cert:
        raise ValueError("Empresa prestadora não possui um Certificado Digital A1 ativo.")

    cert_bytes = decrypt_data(cert.certificate_data_encrypted)
    cert_password = decrypt_text(cert.password_encrypted)

    # Próximo número sequencial de DPS da empresa
    max_dps = db.scalar(
        select(func.max(NfseDocument.dps_number)).where(
            NfseDocument.company_id == payload.company_id,
            NfseDocument.tenant_id == tenant_id,
        )
    )
    next_dps_number = (max_dps or 0) + 1
    dps_series = "1"

    clean_cnpj = re.sub(r"\D", "", company.cnpj or "").zfill(14)
    dps_id = f"DPS{clean_cnpj}{dps_series.zfill(5)}{str(next_dps_number).zfill(15)}"

    # Cálculos Fiscais do ISS e Retenções
    base_calc = max(0.0, payload.service_amount - payload.deductions_amount - payload.discount_unconditional)
    rate_decimal = payload.iss_rate / 100.0 if payload.iss_rate > 0.1 else payload.iss_rate
    iss_amt = round(base_calc * rate_decimal, 2)
    iss_retained_amt = iss_amt if payload.iss_withheld else 0.0

    # Valor líquido da NFS-e
    net_amt = round(
        payload.service_amount
        - payload.deductions_amount
        - payload.discount_unconditional
        - iss_retained_amt
        - payload.pis_retained
        - payload.cofins_retained
        - payload.csll_retained
        - payload.ir_retained
        - payload.inss_retained,
        2,
    )

    doc = NfseDocument(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=payload.company_id,
        customer_id=payload.customer_id,
        dps_number=next_dps_number,
        dps_series=dps_series,
        dps_id=dps_id,
        provider_type=payload.provider_type or "NATIONAL",
        status=NfseStatus.DRAFT.value,
        environment=2, # Homologação por padrão
        service_code_lc116=payload.service_code_lc116,
        national_tax_code=payload.national_tax_code,
        service_description=payload.service_description,
        municipality_ibge=payload.municipality_ibge,
        iss_taxation_type=payload.iss_taxation_type,
        taker_document=re.sub(r"\D", "", payload.taker_document),
        taker_name=payload.taker_name,
        taker_email=payload.taker_email,
        taker_uf=payload.taker_uf,
        service_amount=payload.service_amount,
        deductions_amount=payload.deductions_amount,
        discount_unconditional=payload.discount_unconditional,
        discount_conditional=payload.discount_conditional,
        iss_rate=rate_decimal,
        iss_amount=iss_amt,
        iss_withheld=payload.iss_withheld,
        iss_retained_amount=iss_retained_amt,
        pis_retained=payload.pis_retained,
        cofins_retained=payload.cofins_retained,
        csll_retained=payload.csll_retained,
        ir_retained=payload.ir_retained,
        inss_retained=payload.inss_retained,
        net_amount=net_amt,
    )
    db.add(doc)
    db.flush()

    # Seleciona Adapter e Efetua Emissão
    adapter = NfseProviderFactory.get_adapter(doc.provider_type)
    result = adapter.emit_nfse(db, company, doc, cert_bytes, cert_password)

    # Trilha de Auditoria
    if user_id:
        audit = AuditLog(
            tenant_id=tenant_id,
            company_id=payload.company_id,
            user_id=user_id,
            action="NFSE_EMITTED",
            entity="nfse_document",
            entity_id=doc.id,
            after_data=json.dumps({
                "dps_number": doc.dps_number,
                "nfse_number": doc.nfse_number,
                "access_key_national": doc.access_key_national,
                "status": doc.status,
                "net_amount": float(doc.net_amount or 0.0),
            }),
        )
        db.add(audit)
        db.commit()

    return result


def cancel_nfse_document(
    db: Session,
    tenant_id: uuid.UUID,
    nfse_id: uuid.UUID,
    payload: NfseCancelRequest,
    user_id: Optional[uuid.UUID] = None,
) -> NfseEmissionResult:
    doc = db.scalar(
        select(NfseDocument).where(NfseDocument.id == nfse_id, NfseDocument.tenant_id == tenant_id)
    )
    if not doc:
        raise ValueError("NFS-e não encontrada.")

    company = db.scalar(
        select(Company).where(Company.id == doc.company_id, Company.tenant_id == tenant_id)
    )
    if not company:
        raise ValueError("Empresa prestadora não encontrada.")

    cert = db.scalar(
        select(FiscalCertificate).where(
            FiscalCertificate.company_id == doc.company_id,
            FiscalCertificate.tenant_id == tenant_id,
            FiscalCertificate.is_active == True,
        )
    )
    if not cert:
        raise ValueError("Certificado Digital A1 ativo não encontrado para efetuar cancelamento.")

    cert_bytes = decrypt_data(cert.certificate_data_encrypted)
    cert_password = decrypt_text(cert.password_encrypted)

    adapter = NfseProviderFactory.get_adapter(doc.provider_type)
    result = adapter.cancel_nfse(db, company, doc, payload.justification, cert_bytes, cert_password)

    if user_id:
        audit = AuditLog(
            tenant_id=tenant_id,
            company_id=doc.company_id,
            user_id=user_id,
            action="NFSE_CANCELLED",
            entity="nfse_document",
            entity_id=doc.id,
            after_data=json.dumps({
                "nfse_number": doc.nfse_number,
                "justification": payload.justification,
                "status": doc.status,
            }),
        )
        db.add(audit)
        db.commit()

    return result
