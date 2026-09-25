from typing import List, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api import deps
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.tenant import TenantCreate, TenantResponse, TenantUpdate

router = APIRouter()


@router.get("", response_model=List[TenantResponse], summary="Listar Tenants")
def list_tenants(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("usuarios.gerenciar"))
) -> Any:
    """
    Lista todos os tenants cadastrados. Requer permissão 'usuarios.gerenciar'.
    """
    tenants = db.scalars(select(Tenant)).all()
    return tenants


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED, summary="Criar Tenant")
def create_tenant(
    tenant_in: TenantCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("usuarios.gerenciar"))
) -> Any:
    """
    Cria um novo Tenant na plataforma.
    """
    tenant = Tenant(
        name=tenant_in.name,
        document=tenant_in.document,
        is_active=tenant_in.is_active
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@router.get("/{tenant_id}", response_model=TenantResponse, summary="Obter Tenant por ID")
def get_tenant(
    tenant_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Obtém detalhes do Tenant.
    """
    if not current_user.is_superuser and current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Acesso não autorizado a este tenant")

    tenant = db.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    return tenant
