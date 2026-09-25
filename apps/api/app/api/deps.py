from typing import Generator, List, Callable
from uuid import UUID
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import decode_token
from app.models.user import User
from app.models.tenant import Tenant
from app.models.company import Company
from app.models.rbac import Role, Permission

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


def get_db() -> Generator[Session, None, None]:
    """Provides a database session generator per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    """Decodes JWT access token and retrieves the authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = UUID(user_id_str)
    except Exception:
        raise credentials_exception

    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise credentials_exception
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensures the authenticated user account is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta de usuário inativa"
        )
    return current_user


def get_user_permissions(db: Session, user: User) -> List[str]:
    """Retrieves all distinct permission codes assigned to a user via roles."""
    if user.is_superuser:
        # Superuser has all permissions implicitly
        all_perms = db.scalars(select(Permission.code)).all()
        return list(all_perms)

    # Collect permissions from user's assigned roles
    perm_codes = set()
    for role in user.roles:
        for perm in role.permissions:
            perm_codes.add(perm.code)

    return list(perm_codes)


def require_permission(permission_code: str) -> Callable:
    """Factory function for FastAPI dependency enforcing RBAC permission."""
    def permission_checker(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.is_superuser:
            return current_user

        user_perms = get_user_permissions(db, current_user)
        if permission_code not in user_perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado: permissão '{permission_code}' necessária"
            )
        return current_user

    return permission_checker
