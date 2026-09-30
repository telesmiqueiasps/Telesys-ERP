import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_db
from app.models.nfse_document import NfseDocument
from app.schemas.nfse import (
    NfseCreateRequest,
    NfseCancelRequest,
    NfseEmissionResult,
    NfseResponse,
)
from app.services.nfse_service import create_and_emit_nfse, cancel_nfse_document

router = APIRouter()

# Fixed tenant ID mock for current stage
MOCK_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.post("/", response_model=NfseEmissionResult, status_code=201)
def emit_nfse(
    payload: NfseCreateRequest,
    db: Session = Depends(get_db),
):
    """
    Cria rascunho de DPS e transmite NFS-e via NfseProvider (Padrão Nacional SEFIN ou Adapter Municipal).
    Calcula ISS e retenções federais.
    """
    try:
        result = create_and_emit_nfse(
            db=db,
            tenant_id=MOCK_TENANT_ID,
            payload=payload,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na emissão de NFS-e: {str(e)}")


@router.get("/", response_model=List[NfseResponse])
def list_nfse(
    company_id: uuid.UUID = Query(...),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Lista Notas Fiscais de Serviço Eletrônicas da empresa.
    """
    stmt = select(NfseDocument).where(
        NfseDocument.company_id == company_id,
        NfseDocument.tenant_id == MOCK_TENANT_ID,
    )
    if status:
        stmt = stmt.where(NfseDocument.status == status)

    docs = db.scalars(stmt.order_by(NfseDocument.created_at.desc())).all()
    return docs


@router.get("/{nfse_id}", response_model=NfseResponse)
def get_nfse(
    nfse_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Obtém detalhes de uma NFS-e pelo ID.
    """
    doc = db.scalar(
        select(NfseDocument).where(
            NfseDocument.id == nfse_id,
            NfseDocument.tenant_id == MOCK_TENANT_ID,
        )
    )
    if not doc:
        raise HTTPException(status_code=404, detail="NFS-e não encontrada.")
    return doc


@router.post("/{nfse_id}/cancel", response_model=NfseEmissionResult)
def cancel_nfse(
    nfse_id: uuid.UUID,
    payload: NfseCancelRequest,
    db: Session = Depends(get_db),
):
    """
    Cancela uma NFS-e emitida.
    """
    try:
        result = cancel_nfse_document(
            db=db,
            tenant_id=MOCK_TENANT_ID,
            nfse_id=nfse_id,
            payload=payload,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no cancelamento da NFS-e: {str(e)}")


@router.get("/{nfse_id}/xml")
def download_nfse_xml(
    nfse_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Retorna o XML da NFS-e (procNFSe ou DPS assinada).
    """
    doc = db.scalar(
        select(NfseDocument).where(
            NfseDocument.id == nfse_id,
            NfseDocument.tenant_id == MOCK_TENANT_ID,
        )
    )
    if not doc:
        raise HTTPException(status_code=404, detail="NFS-e não encontrada.")

    xml_content = doc.nfse_proc_xml or doc.signed_dps_xml or doc.dps_raw_xml
    if not xml_content:
        raise HTTPException(status_code=404, detail="XML da NFS-e não disponível.")

    return Response(content=xml_content, media_type="application/xml")
