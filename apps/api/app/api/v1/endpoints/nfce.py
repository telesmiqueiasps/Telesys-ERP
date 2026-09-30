import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.sale import Sale
from app.models.nfe_document import NfeDocument, NfeStatus
from app.schemas.nfce import NfceEmitResponse, DanfeNfceResponse
from app.services.nfce_service import NfceService
from app.services.danfe_nfce_renderer import DanfeNfceRenderer
from app.services.qr_code_generator import NfceQrCodeGenerator
from app.services.sefaz_adapter import SefazServiceAdapter, SefazRequest

router = APIRouter()


@router.post("/emit/{sale_id}", response_model=NfceEmitResponse, status_code=status.HTTP_201_CREATED)
def emit_nfce_for_sale_endpoint(
    sale_id: uuid.UUID,
    issue_type: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Emite obrigatoriamente a NFC-e (Modelo 65) para uma venda realizada no PDV.
    Executa cálculos fiscais, gera XML, assina com Certificado A1 e transmite à SEFAZ.
    Se houver queda de comunicação com a SEFAZ, o documento entra automaticamente em Contingência Offline (tpEmis 9).
    """
    sale = db.scalar(
        select(Sale).where(
            Sale.id == sale_id,
            Sale.tenant_id == current_user.tenant_id,
        )
    )
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venda não encontrada.",
        )

    try:
        nfe_doc = NfceService.emit_nfce_for_sale(
            db=db,
            tenant_id=current_user.tenant_id,
            company_id=sale.company_id,
            sale=sale,
            issue_type=issue_type,
            user_id=current_user.id,
        )

        qr_code_url = getattr(nfe_doc, "qr_code_url", "")
        url_chave = getattr(nfe_doc, "url_chave", "")

        return NfceEmitResponse(
            nfe_id=nfe_doc.id,
            sale_id=sale.id,
            access_key=nfe_doc.access_key,
            number=nfe_doc.number,
            series=nfe_doc.series,
            model="65",
            status=nfe_doc.status,
            protocol_number=nfe_doc.protocol_number,
            qr_code_url=qr_code_url,
            url_chave=url_chave,
            danfe_url=f"/api/v1/nfce/{nfe_doc.id}/danfe",
            created_at=nfe_doc.created_at,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Falha na emissão da NFC-e: {str(e)}",
        )


@router.get("/{nfe_id}/danfe", response_class=HTMLResponse)
def get_danfe_html(
    nfe_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna o DANFE NFC-e pronto para impressão em impressora térmica (80mm/58mm).
    """
    nfe_doc = db.scalar(
        select(NfeDocument).where(
            NfeDocument.id == nfe_id,
            NfeDocument.tenant_id == current_user.tenant_id,
        )
    )
    if not nfe_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NFC-e não encontrada.",
        )

    qr_code_url = NfceQrCodeGenerator.generate_qr_code_str(
        access_key=nfe_doc.access_key,
        environment=nfe_doc.environment,
        uf=nfe_doc.issuer_uf,
        issue_date_hex=nfe_doc.created_at.strftime("%d%m%Y"),
        vNF=float(nfe_doc.vNF),
        vICMS=float(nfe_doc.vICMS),
        digest_value_hex="0000000000000000000000000000000000000000",
    )
    url_chave = NfceQrCodeGenerator.get_url_chave(nfe_doc.issuer_uf, nfe_doc.environment)

    html_content = DanfeNfceRenderer.render_html(
        doc=nfe_doc,
        qr_code_url=qr_code_url,
        url_chave=url_chave,
    )
    return HTMLResponse(content=html_content, status_code=200)


from app.services.fiscal_reconciler import FiscalReconciler


@router.post("/transmit-contingency-queue")
def transmit_contingency_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Varre e transmite à SEFAZ todas as NFC-es emitidas em Contingência Offline (status AUTHORIZED_OFFLINE).
    Utiliza o FiscalReconciler com tratamento de duplicidade e consulta de protocolo.
    """
    offline_docs = db.scalars(
        select(NfeDocument).where(
            NfeDocument.tenant_id == current_user.tenant_id,
            NfeDocument.status == "AUTHORIZED_OFFLINE",
            NfeDocument.model == "65",
        )
    ).all()

    authorized_count = 0
    reconciled_count = 0
    rejected_count = 0
    pending_count = 0

    for doc in offline_docs:
        res = FiscalReconciler.reconcile_and_transmit_contingency_doc(db, doc)
        st = res.get("status")
        if st == "AUTHORIZED":
            authorized_count += 1
        elif st == "RECONCILED_AUTHORIZED":
            reconciled_count += 1
        elif st in ("REJECTED", "REJECTED_DUPLICATE"):
            rejected_count += 1
        else:
            pending_count += 1

    return {
        "total_offline": len(offline_docs),
        "transmitted_authorized": authorized_count,
        "reconciled_authorized": reconciled_count,
        "rejected": rejected_count,
        "pending": pending_count,
    }


@router.get("/contingency-queue")
def get_contingency_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lista os documentos fiscais armazenados na fila de contingência offline pendentes de envio.
    """
    offline_docs = db.scalars(
        select(NfeDocument).where(
            NfeDocument.tenant_id == current_user.tenant_id,
            NfeDocument.status == "AUTHORIZED_OFFLINE",
        ).order_by(NfeDocument.created_at.asc())
    ).all()

    return [
        {
            "id": d.id,
            "sale_id": d.sale_id,
            "access_key": d.access_key,
            "number": d.number,
            "series": d.series,
            "vNF": float(d.vNF),
            "created_at": d.created_at,
            "protocol_number": d.protocol_number,
        }
        for d in offline_docs
    ]
