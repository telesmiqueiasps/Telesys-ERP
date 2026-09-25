from typing import List, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api import deps
from app.core import security
from app.models.user import User
from app.models.rbac import Role
from app.schemas.user import UserCreate, UserResponse, UserUpdate, UserWithRolesResponse

router = APIRouter()


@router.get("", response_model=List[UserWithRolesResponse], summary="Listar Usuários do Tenant")
def list_users(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("usuarios.gerenciar"))
) -> Any:
    """
    Lista todos os usuários do tenant atual.
    """
    users = db.scalars(
        select(User).where(User.tenant_id == current_user.tenant_id)
    ).all()
    return users


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Criar Usuário")
def create_user(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("usuarios.gerenciar"))
) -> Any:
    """
    Cria um novo usuário e atribui funções (roles).
    """
    if not current_user.is_superuser and user_in.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Não é permitido criar usuários em outro tenant")

    existing_user = db.scalar(select(User).where(User.email == user_in.email))
    if existing_user:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado no sistema")

    hashed_password = security.get_password_hash(user_in.password)
    user = User(
        tenant_id=user_in.tenant_id,
        name=user_in.name,
        email=user_in.email,
        password_hash=hashed_password,
        is_active=user_in.is_active,
        is_superuser=user_in.is_superuser if current_user.is_superuser else False
    )

    if user_in.role_ids:
        roles = db.scalars(select(Role).where(Role.id.in_(user_in.role_ids))).all()
        user.roles = list(roles)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserWithRolesResponse, summary="Obter Usuário por ID")
def get_user(
    user_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("usuarios.gerenciar"))
) -> Any:
    """
    Obtém detalhes do usuário.
    """
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if not current_user.is_superuser and user.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acesso não autorizado")

    return user
