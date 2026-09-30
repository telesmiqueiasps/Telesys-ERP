import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_db
from app.models.fiscal_update import FiscalUpdateAudit
from app.schemas.fiscal_update import (
    FiscalSchemaVersionCreate,
    FiscalRuleApplyRequest,
    FiscalRuleRejectRequest,
    FiscalSchemaVersionResponse,
    FiscalUpdateAuditResponse,
)
from app.services.fiscal_update_service import (
    register_technical_note_update,
    approve_and_apply_fiscal_update,
    reject_fiscal_update,
    get_pending_fiscal_updates,
    get_all_fiscal_schema_versions,
)

router = APIRouter()

# Fixed tenant ID mock for current stage
MOCK_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.get("/versions", response_model=List[FiscalSchemaVersionResponse], status_code=200)
def list_fiscal_schema_versions(
    company_id: uuid.UUID = Query(..., description="ID da Empresa"),
    db: Session = Depends(get_db),
):
    """
    Lista todas as versões de Schemas e Notas Técnicas SEFAZ cadastradas.
    """
    try:
        return get_all_fiscal_schema_versions(db, MOCK_TENANT_ID, company_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar versões fiscais: {str(e)}")


@router.get("/pending", response_model=List[FiscalSchemaVersionResponse], status_code=200)
def list_pending_fiscal_updates(
    company_id: uuid.UUID = Query(..., description="ID da Empresa"),
    db: Session = Depends(get_db),
):
    """
    Lista todas as atualizações fiscais/Notas Técnicas pendentes de aprovação explícita pelo usuário.
    """
    try:
        return get_pending_fiscal_updates(db, MOCK_TENANT_ID, company_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar atualizações pendentes: {str(e)}")


@router.post("/register", response_model=FiscalSchemaVersionResponse, status_code=201)
def register_fiscal_update(
    payload: FiscalSchemaVersionCreate,
    db: Session = Depends(get_db),
):
    """
    Registra nova Nota Técnica / versão de Schema SEFAZ.
    REGRA CRÍTICA: Não atualiza silenciosamente. O registro nasce em estado PENDING_APPROVAL aguardando aprovação explícita.
    """
    try:
        ver = register_technical_note_update(
            db=db,
            tenant_id=MOCK_TENANT_ID,
            payload=payload,
        )
        return ver
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao registrar atualização fiscal: {str(e)}")


@router.post("/{version_id}/apply", response_model=FiscalSchemaVersionResponse, status_code=200)
def apply_fiscal_update(
    version_id: uuid.UUID,
    company_id: uuid.UUID = Query(..., description="ID da Empresa"),
    payload: FiscalRuleApplyRequest = ...,
    db: Session = Depends(get_db),
):
    """
    Aplica explicitamente uma versão de Nota Técnica / regra fiscal em Homologação ou Produção.
    Requer confirmação do usuário (user_id) impedindo atualizações silenciosas.
    """
    try:
        ver = approve_and_apply_fiscal_update(
            db=db,
            tenant_id=MOCK_TENANT_ID,
            company_id=company_id,
            version_id=version_id,
            payload=payload,
        )
        return ver
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao aplicar atualização fiscal: {str(e)}")


@router.post("/{version_id}/reject", response_model=FiscalSchemaVersionResponse, status_code=200)
def reject_fiscal_update_endpoint(
    version_id: uuid.UUID,
    company_id: uuid.UUID = Query(..., description="ID da Empresa"),
    payload: FiscalRuleRejectRequest = ...,
    db: Session = Depends(get_db),
):
    """
    Rejeita a aplicação de uma Nota Técnica / atualização fiscal com justificativa detalhada.
    """
    try:
        ver = reject_fiscal_update(
            db=db,
            tenant_id=MOCK_TENANT_ID,
            company_id=company_id,
            version_id=version_id,
            payload=payload,
        )
        return ver
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao rejeitar atualização fiscal: {str(e)}")


@router.get("/audit-trail", response_model=List[FiscalUpdateAuditResponse], status_code=200)
def get_fiscal_update_audit_trail(
    company_id: uuid.UUID = Query(..., description="ID da Empresa"),
    db: Session = Depends(get_db),
):
    """
    Retorna a trilha auditável imutável de todas as ações tomadas no Centro de Atualizações Fiscais.
    """
    try:
        audits = list(
            db.scalars(
                select(FiscalUpdateAudit)
                .where(
                    FiscalUpdateAudit.company_id == company_id,
                    FiscalUpdateAudit.tenant_id == MOCK_TENANT_ID,
                )
                .order_by(FiscalUpdateAudit.created_at.desc())
            ).all()
        )
        return audits
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter trilha de auditoria: {str(e)}")
