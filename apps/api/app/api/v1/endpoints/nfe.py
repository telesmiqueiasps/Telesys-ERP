import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.nfe_document import NfeDocument
from app.schemas.nfe import NfeDocumentCreate, NfeDocumentResponse
from app.services.nfe import create_nfe_draft, sign_nfe_document, attach_authorization_protocol

router = APIRouter()


@router.post("/draft", response_model=NfeDocumentResponse, status_code=status.HTTP_201_CREATED)
def create_draft(
    payload: NfeDocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cria um rascunho de NF-e Modelo 55, resolvendo os tributos via TaxEngine e gerando a Chave de 44 dígitos.
    """
    try:
        return create_nfe_draft(db, current_user.tenant_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar rascunho da NF-e: {str(e)}")


@router.get("", response_model=List[NfeDocumentResponse])
def list_nfe_documents(
    company_id: uuid.UUID = Query(..., description="ID da Empresa"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lista todas as Notas Fiscais Eletrônicas Modelo 55 da empresa.
    """
    docs = db.scalars(
        select(NfeDocument)
        .where(
            NfeDocument.company_id == company_id,
            NfeDocument.tenant_id == current_user.tenant_id,
        )
        .order_by(NfeDocument.created_at.desc())
    ).all()
    return list(docs)


@router.get("/{nfe_id}", response_model=NfeDocumentResponse)
def get_nfe_document(
    nfe_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna os detalhes de uma NF-e Modelo 55.
    """
    doc = db.scalar(
        select(NfeDocument).where(NfeDocument.id == nfe_id, NfeDocument.tenant_id == current_user.tenant_id)
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Nota Fiscal Eletrônica não encontrada.")
    return doc


@router.post("/{nfe_id}/sign", response_model=NfeDocumentResponse)
def sign_nfe(
    nfe_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Assina digitalmente o XML da NF-e usando o Certificado Digital A1 ativo da empresa.
    """
    try:
        return sign_nfe_document(db, current_user.tenant_id, nfe_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao assinar a NF-e: {str(e)}")


@router.post("/{nfe_id}/authorize-mock", response_model=NfeDocumentResponse)
def authorize_nfe_mock(
    nfe_id: uuid.UUID,
    protocol_number: str = Query("135260001234567", description="Número de protocolo SEFAZ"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Simula a anexação do protocolo de autorização SEFAZ e gera o XML de distribuição <nfeProc>.
    """
    try:
        return attach_authorization_protocol(db, current_user.tenant_id, nfe_id, protocol_number=protocol_number)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{nfe_id}/xml/raw")
def get_raw_xml(
    nfe_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna o XML rascunho não assinado.
    """
    doc = db.scalar(
        select(NfeDocument).where(NfeDocument.id == nfe_id, NfeDocument.tenant_id == current_user.tenant_id)
    )
    if not doc or not doc.raw_xml:
        raise HTTPException(status_code=404, detail="XML rascunho não disponível.")
    return Response(content=doc.raw_xml, media_type="application/xml")


@router.get("/{nfe_id}/xml/signed")
def get_signed_xml(
    nfe_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna o XML assinado com o Certificado Digital A1.
    """
    doc = db.scalar(
        select(NfeDocument).where(NfeDocument.id == nfe_id, NfeDocument.tenant_id == current_user.tenant_id)
    )
    if not doc or not doc.signed_xml:
        raise HTTPException(status_code=404, detail="XML assinado não disponível.")
    return Response(content=doc.signed_xml, media_type="application/xml")


@router.get("/{nfe_id}/xml/proc")
def get_proc_xml(
    nfe_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna o XML de distribuição completo (<nfeProc>) com protocolo de autorização SEFAZ.
    """
    doc = db.scalar(
        select(NfeDocument).where(NfeDocument.id == nfe_id, NfeDocument.tenant_id == current_user.tenant_id)
    )
    if not doc or not doc.proc_xml:
        raise HTTPException(status_code=404, detail="XML de distribuição nfeProc não disponível.")
    return Response(content=doc.proc_xml, media_type="application/xml")
