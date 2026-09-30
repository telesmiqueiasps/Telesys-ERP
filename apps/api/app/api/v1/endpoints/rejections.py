import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.nfe_document import NfeDocument
from app.models.company import Company
from app.models.company_fiscal import FiscalCompanyConfig
from app.models.nfe_rejection import NfeRejectionLog
from app.schemas.rejections import (
    SefazRejectionCatalogEntry,
    PreValidationResult,
    NfeRejectionLogRead,
)
from app.services.sefaz_rejections_catalog import SefazRejectionsCatalog
from app.services.fiscal_pre_validator import FiscalPreValidator

router = APIRouter()


@router.get("/catalog", response_model=List[SefazRejectionCatalogEntry])
def list_rejections_catalog():
    """
    Retorna o Catálogo Oficial de Rejeições SEFAZ com diagnósticos e soluções operacionais.
    """
    return SefazRejectionsCatalog.list_catalog()


@router.get("/catalog/{code}", response_model=SefazRejectionCatalogEntry)
def get_rejection_catalog_entry(code: int):
    """
    Obtém os detalhes de uma rejeição específica por código cStat.
    """
    entry = SefazRejectionsCatalog.get_rejection(code)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rejeição SEFAZ código {code} não encontrada no catálogo oficial.",
        )
    return entry


@router.post("/pre-validate/{nfe_id}", response_model=PreValidationResult)
def pre_validate_nfe(
    nfe_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Executa a pré-validação fiscal estrita da NF-e Modelo 55 antes do envio para a SEFAZ.
    Verifica CNPJ/CPF, Chave de Acesso (Módulo 11), NCM (8 dig), CEST (7 dig), IE e CRT vs CST/CSOSN.
    """
    nfe = db.scalar(
        select(NfeDocument).where(
            NfeDocument.id == nfe_id,
            NfeDocument.tenant_id == current_user.tenant_id,
        )
    )
    if not nfe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NF-e não encontrada.",
        )

    company = db.scalar(
        select(Company).where(
            Company.id == nfe.company_id,
            Company.tenant_id == current_user.tenant_id,
        )
    )
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa emitente não encontrada.",
        )

    fiscal_config = db.scalar(
        select(FiscalCompanyConfig).where(
            FiscalCompanyConfig.company_id == company.id,
            FiscalCompanyConfig.tenant_id == current_user.tenant_id,
        )
    )

    emit_crt = fiscal_config.crt if fiscal_config else 1
    emit_ie = getattr(company, "state_registration", None) or getattr(company, "ie", None) or ""

    return FiscalPreValidator.validate(
        nfe=nfe,
        emit_cnpj=company.cnpj or "",
        emit_crt=emit_crt,
        emit_ie=emit_ie,
    )


@router.get("/history/{nfe_id}", response_model=List[NfeRejectionLogRead])
def get_nfe_rejection_history(
    nfe_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Histórico auditável de rejeições retornadas pela SEFAZ para uma determinada NF-e.
    """
    logs = db.scalars(
        select(NfeRejectionLog)
        .where(
            NfeRejectionLog.nfe_id == nfe_id,
            NfeRejectionLog.tenant_id == current_user.tenant_id,
        )
        .order_by(NfeRejectionLog.created_at.desc())
    ).all()
    return list(logs)
