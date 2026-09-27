import json
import uuid
from typing import List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, desc

from app.api import deps
from app.models.user import User
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogResponse

router = APIRouter()


def log_audit_action(
    db: Session,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    action: str,
    entity: str,
    entity_id: Optional[uuid.UUID] = None,
    before_data: Optional[Any] = None,
    after_data: Optional[Any] = None,
    device_id: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """
    Função utilitária para registrar ações sensíveis na tabela audit_logs.
    """
    str_before = json.dumps(before_data, default=str, ensure_ascii=False) if before_data is not None else None
    str_after = json.dumps(after_data, default=str, ensure_ascii=False) if after_data is not None else None

    log = AuditLog(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=company_id,
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        before_data=str_before,
        after_data=str_after,
        device_id=device_id,
        ip_address=ip_address,
    )
    db.add(log)
    return log


@router.get("/logs", response_model=List[AuditLogResponse], summary="Consultar Histórico de Auditoria")
def get_audit_logs(
    company_id: uuid.UUID = Query(..., description="ID da empresa"),
    entity: Optional[str] = Query(None, description="Filtrar por módulo/entidade"),
    action: Optional[str] = Query(None, description="Filtrar por tipo de ação"),
    user_id: Optional[uuid.UUID] = Query(None, description="Filtrar por usuário"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retorna o histórico de auditoria e rastreabilidade para administradores.
    """
    stmt = (
        select(AuditLog)
        .options(selectinload(AuditLog.user))
        .where(
            AuditLog.company_id == company_id,
            AuditLog.tenant_id == current_user.tenant_id
        )
    )

    if entity:
        stmt = stmt.where(AuditLog.entity == entity)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)

    stmt = stmt.order_by(desc(AuditLog.created_at)).limit(limit)
    logs = db.scalars(stmt).all()

    result = []
    for log in logs:
        result.append(
            AuditLogResponse(
                id=log.id,
                tenant_id=log.tenant_id,
                company_id=log.company_id,
                user_id=log.user_id,
                user_name=log.user.name if log.user else "Sistema",
                action=log.action,
                entity=log.entity,
                entity_id=log.entity_id,
                before_data=log.before_data,
                after_data=log.after_data,
                device_id=log.device_id,
                ip_address=log.ip_address,
                created_at=log.created_at,
            )
        )

    return result


@router.get("/logs/{log_id}", response_model=AuditLogResponse, summary="Obter Detalhes do Log de Auditoria")
def get_audit_log_detail(
    log_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retorna os detalhes completos de um registro de auditoria.
    """
    stmt = (
        select(AuditLog)
        .options(selectinload(AuditLog.user))
        .where(
            AuditLog.id == log_id,
            AuditLog.tenant_id == current_user.tenant_id
        )
    )
    log = db.scalar(stmt)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de auditoria não encontrado."
        )

    return AuditLogResponse(
        id=log.id,
        tenant_id=log.tenant_id,
        company_id=log.company_id,
        user_id=log.user_id,
        user_name=log.user.name if log.user else "Sistema",
        action=log.action,
        entity=log.entity,
        entity_id=log.entity_id,
        before_data=log.before_data,
        after_data=log.after_data,
        device_id=log.device_id,
        ip_address=log.ip_address,
        created_at=log.created_at,
    )
