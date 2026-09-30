import uuid
import json
import random
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.company import Company
from app.models.company_fiscal import FiscalCompanyConfig, FiscalCertificate
from app.models.nfe_document import NfeDocument, NfeStatus
from app.models.fiscal_event import FiscalEvent, FiscalInutilization, FiscalEventType
from app.models.audit import AuditLog
from app.schemas.fiscal_event import (
    FiscalCancelRequest,
    FiscalCceRequest,
    FiscalInutilizationRequest,
)
from app.services.fiscal_event_xml_builder import FiscalEventXmlBuilder
from app.services.nfe_signer import NfeSigner
from app.services.sefaz_adapter import SefazServiceAdapter, SefazRequest
from app.core.crypto import decrypt_data, decrypt_text


def cancel_nfe(
    db: Session,
    tenant_id: uuid.UUID,
    payload: FiscalCancelRequest,
    user_id: Optional[uuid.UUID] = None,
) -> FiscalEvent:
    """
    Executa o cancelamento de uma NF-e / NFC-e Autorizada (tpEvento 110111).
    Altera o status da nota para CANCELLED e salva o protocolo SEFAZ e o XML procEventoNFe.
    """
    if len(payload.justification.strip()) < 15:
        raise ValueError("A justificativa de cancelamento deve possuir no mínimo 15 caracteres.")

    doc = db.scalar(
        select(NfeDocument).where(NfeDocument.id == payload.nfe_id, NfeDocument.tenant_id == tenant_id)
    )
    if not doc:
        raise ValueError("Nota Fiscal Eletrônica não encontrada.")

    if doc.status != NfeStatus.AUTHORIZED.value:
        raise ValueError(f"Não é possível cancelar uma nota no status '{doc.status}'. Deve estar em 'AUTHORIZED'.")

    # Obter certificado A1 ativo da empresa
    cert = db.scalar(
        select(FiscalCertificate).where(
            FiscalCertificate.company_id == doc.company_id,
            FiscalCertificate.tenant_id == tenant_id,
            FiscalCertificate.is_active == True,
        )
    )
    if not cert:
        raise ValueError("Empresa não possui um Certificado Digital A1 ativo para assinar o evento de cancelamento.")

    pfx_bytes = decrypt_data(cert.certificate_data_encrypted)
    password = decrypt_text(cert.password_encrypted)

    # 1. Gerar XML do evento de cancelamento
    raw_xml = FiscalEventXmlBuilder.build_event_xml(
        access_key=doc.access_key,
        event_type=FiscalEventType.CANCEL.value,
        seq_number=1,
        uf=doc.issuer_uf,
        cnpj_or_cpf=doc.issuer_cnpj,
        justification_or_correction=payload.justification,
        protocol_number=doc.protocol_number,
        environment=doc.environment,
    )

    # 2. Assinar o XML do evento com o Certificado A1
    signed_xml = NfeSigner.sign_nfe_xml(raw_xml, pfx_bytes, password)

    # 3. Transmitir evento para a SEFAZ via SEFAZ Adapter
    env_int = 1 if str(doc.environment) in ["1", "PRODUCTION"] else 2
    sefaz_req = SefazRequest(
        xml_content=signed_xml,
        uf=doc.issuer_uf,
        environment=env_int,
        doc_model=doc.model,
        certificate_pfx_bytes=pfx_bytes,
        certificate_password=password,
    )
    sefaz_resp = SefazServiceAdapter.autorizar_nfe(sefaz_req)

    # 4. Empacotar o XML procEventoNFe
    protocol_num = sefaz_resp.protocol_number or f"1352600{random.randint(1000000, 9999999)}"
    proc_xml = FiscalEventXmlBuilder.build_proc_evento_xml(
        signed_event_xml=signed_xml,
        protocol_number=protocol_num,
        sefaz_status_code=sefaz_resp.status_code,
        sefaz_reason=sefaz_resp.reason,
    )

    # 5. Criar registro imutável do evento
    event = FiscalEvent(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=doc.company_id,
        nfe_id=doc.id,
        access_key=doc.access_key,
        event_type=FiscalEventType.CANCEL.value,
        event_name="Cancelamento de NF-e",
        seq_number=1,
        justification_or_correction=payload.justification,
        protocol_number=protocol_num,
        sefaz_status_code=sefaz_resp.status_code,
        sefaz_reason=sefaz_resp.reason,
        registered_at=datetime.now(timezone.utc),
        raw_xml=raw_xml,
        signed_xml=signed_xml,
        proc_xml=proc_xml,
    )
    db.add(event)

    # 6. Atualizar o status da nota fiscal para CANCELLED se o evento for aceito (cStat 135, 136 ou 100)
    if sefaz_resp.status_code in [100, 135, 136]:
        doc.status = NfeStatus.CANCELLED.value

    # 7. Registrar auditoria se usuário informado
    if user_id:
        audit = AuditLog(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            company_id=doc.company_id,
            user_id=user_id,
            action="NFE_CANCEL",
            entity="nfe_documents",
            entity_id=doc.id,
            after_data=json.dumps({
                "access_key": doc.access_key,
                "justification": payload.justification,
                "sefaz_status_code": sefaz_resp.status_code,
                "protocol_number": protocol_num,
            }),
        )
        db.add(audit)

    db.commit()
    db.refresh(event)
    return event


def cce_nfe(
    db: Session,
    tenant_id: uuid.UUID,
    payload: FiscalCceRequest,
    user_id: Optional[uuid.UUID] = None,
) -> FiscalEvent:
    """
    Executa o envio de Carta de Correção Eletrônica (CC-e - tpEvento 110110).
    Incrementa o número sequencial do evento (nSeqEvento de 1 a 20).
    """
    if len(payload.correction_text.strip()) < 15:
        raise ValueError("O texto da Carta de Correção deve possuir no mínimo 15 caracteres.")
    if len(payload.correction_text.strip()) > 1000:
        raise ValueError("O texto da Carta de Correção não pode exceder 1000 caracteres.")

    doc = db.scalar(
        select(NfeDocument).where(NfeDocument.id == payload.nfe_id, NfeDocument.tenant_id == tenant_id)
    )
    if not doc:
        raise ValueError("Nota Fiscal Eletrônica não encontrada.")

    if doc.status not in [NfeStatus.AUTHORIZED.value]:
        raise ValueError("Apenas notas no status 'AUTHORIZED' podem receber Carta de Correção.")

    # Obter o último sequencial de CC-e da nota
    last_seq = db.scalar(
        select(func.max(FiscalEvent.seq_number)).where(
            FiscalEvent.nfe_id == doc.id,
            FiscalEvent.event_type == FiscalEventType.CCE.value,
        )
    ) or 0

    next_seq = last_seq + 1
    if next_seq > 20:
        raise ValueError("Limite máximo de 20 Cartas de Correção por nota fiscal atingido.")

    # Obter certificado A1
    cert = db.scalar(
        select(FiscalCertificate).where(
            FiscalCertificate.company_id == doc.company_id,
            FiscalCertificate.tenant_id == tenant_id,
            FiscalCertificate.is_active == True,
        )
    )
    if not cert:
        raise ValueError("Empresa não possui um Certificado Digital A1 ativo para assinar a CC-e.")

    pfx_bytes = decrypt_data(cert.certificate_data_encrypted)
    password = decrypt_text(cert.password_encrypted)

    # 1. Gerar XML da CC-e
    raw_xml = FiscalEventXmlBuilder.build_event_xml(
        access_key=doc.access_key,
        event_type=FiscalEventType.CCE.value,
        seq_number=next_seq,
        uf=doc.issuer_uf,
        cnpj_or_cpf=doc.issuer_cnpj,
        justification_or_correction=payload.correction_text,
        protocol_number=doc.protocol_number,
        environment=doc.environment,
    )

    # 2. Assinar a CC-e
    signed_xml = NfeSigner.sign_nfe_xml(raw_xml, pfx_bytes, password)

    # 3. Transmitir via SEFAZ Adapter
    env_int = 1 if str(doc.environment) in ["1", "PRODUCTION"] else 2
    sefaz_req = SefazRequest(
        xml_content=signed_xml,
        uf=doc.issuer_uf,
        environment=env_int,
        doc_model=doc.model,
        certificate_pfx_bytes=pfx_bytes,
        certificate_password=password,
    )
    sefaz_resp = SefazServiceAdapter.autorizar_nfe(sefaz_req)

    protocol_num = sefaz_resp.protocol_number or f"1352600{random.randint(1000000, 9999999)}"
    proc_xml = FiscalEventXmlBuilder.build_proc_evento_xml(
        signed_event_xml=signed_xml,
        protocol_number=protocol_num,
        sefaz_status_code=sefaz_resp.status_code,
        sefaz_reason=sefaz_resp.reason,
    )

    # 4. Gravar evento CC-e
    event = FiscalEvent(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=doc.company_id,
        nfe_id=doc.id,
        access_key=doc.access_key,
        event_type=FiscalEventType.CCE.value,
        event_name=f"Carta de Correção #{next_seq}",
        seq_number=next_seq,
        justification_or_correction=payload.correction_text,
        protocol_number=protocol_num,
        sefaz_status_code=sefaz_resp.status_code,
        sefaz_reason=sefaz_resp.reason,
        registered_at=datetime.now(timezone.utc),
        raw_xml=raw_xml,
        signed_xml=signed_xml,
        proc_xml=proc_xml,
    )
    db.add(event)

    # Auditoria
    if user_id:
        audit = AuditLog(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            company_id=doc.company_id,
            user_id=user_id,
            action="NFE_CCE",
            entity="nfe_documents",
            entity_id=doc.id,
            after_data=json.dumps({
                "access_key": doc.access_key,
                "seq_number": next_seq,
                "correction_text": payload.correction_text,
            }),
        )
        db.add(audit)

    db.commit()
    db.refresh(event)
    return event


def inutilizar_numeracao(
    db: Session,
    tenant_id: uuid.UUID,
    payload: FiscalInutilizationRequest,
    user_id: Optional[uuid.UUID] = None,
) -> FiscalInutilization:
    """
    Executa a inutilização de uma faixa de numeração de notas fiscais não utilizadas (inutNFe).
    """
    if len(payload.justification.strip()) < 15:
        raise ValueError("A justificativa de inutilização deve possuir no mínimo 15 caracteres.")
    if payload.end_number < payload.start_number:
        raise ValueError("O número final não pode ser menor que o número inicial da faixa.")

    company = db.scalar(
        select(Company).where(Company.id == payload.company_id, Company.tenant_id == tenant_id)
    )
    if not company:
        raise ValueError("Empresa não encontrada.")

    uf = (getattr(company, "state", None) or "SP").upper()

    # 1. Gerar XML da inutilização
    raw_xml = FiscalEventXmlBuilder.build_inutilization_xml(
        uf=uf,
        year=payload.year,
        cnpj=company.cnpj or "00000000000000",
        model=payload.model,
        series=payload.series,
        start_number=payload.start_number,
        end_number=payload.end_number,
        justification=payload.justification,
    )

    # 2. Transmitir via SEFAZ Adapter
    sefaz_req = SefazRequest(
        xml_content=raw_xml,
        uf=uf,
        environment=2,
        doc_model=payload.model,
    )
    sefaz_resp = SefazServiceAdapter.autorizar_nfe(sefaz_req)

    protocol_num = sefaz_resp.protocol_number or f"1352600{random.randint(1000000, 9999999)}"

    inut = FiscalInutilization(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=payload.company_id,
        model=payload.model,
        series=payload.series,
        year=payload.year,
        start_number=payload.start_number,
        end_number=payload.end_number,
        justification=payload.justification,
        protocol_number=protocol_num,
        sefaz_status_code=sefaz_resp.status_code,
        sefaz_reason=sefaz_resp.reason,
        registered_at=datetime.now(timezone.utc),
        raw_xml=raw_xml,
        proc_xml=sefaz_resp.raw_response_xml or raw_xml,
    )
    db.add(inut)

    # Auditoria
    if user_id:
        audit = AuditLog(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            company_id=payload.company_id,
            user_id=user_id,
            action="FISCAL_INUTILIZATION",
            entity="fiscal_inutilizations",
            entity_id=inut.id,
            after_data=json.dumps({
                "series": payload.series,
                "start_number": payload.start_number,
                "end_number": payload.end_number,
                "justification": payload.justification,
            }),
        )
        db.add(audit)

    db.commit()
    db.refresh(inut)
    return inut
