from typing import List, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.api import deps
from app.models.user import User
from app.models.rbac import Role, Permission
from app.schemas.rbac import PermissionResponse, RoleCreate, RoleResponse, RoleUpdate

router = APIRouter()


@router.get("/permissions", response_model=List[PermissionResponse], summary="Listar Permissões do Sistema")
def list_permissions(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Lista o catálogo completo de permissões disponíveis no sistema.
    """
    permissions = db.scalars(select(Permission).order_by(Permission.module, Permission.code)).all()
    return permissions


@router.get("", response_model=List[RoleResponse], summary="Listar Cargos (Roles)")
def list_roles(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Lista os cargos padrão do sistema e os cargos específicos do tenant.
    """
    roles = db.scalars(
        select(Role).where(
            or_(Role.tenant_id == current_user.tenant_id, Role.is_system == True)
        )
    ).all()
    return roles


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED, summary="Criar Cargo (Role)")
def create_role(
    role_in: RoleCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("usuarios.gerenciar"))
) -> Any:
    """
    Cria um novo cargo customizado e vincula as permissões informadas.
    """
    tenant_id = current_user.tenant_id if not current_user.is_superuser else (role_in.tenant_id or current_user.tenant_id)

    role = Role(
        tenant_id=tenant_id,
        name=role_in.name,
        description=role_in.description,
        is_system=False
    )

    if role_in.permission_ids:
        perms = db.scalars(select(Permission).where(Permission.id.in_(role_in.permission_ids))).all()
        role.permissions = list(perms)

    db.add(role)
    db.commit()
    db.refresh(role)
    return role
