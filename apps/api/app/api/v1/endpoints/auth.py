from datetime import datetime, timedelta, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.tenant import Tenant
from app.models.company import Company
from app.models.refresh_token import RefreshToken
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserMeResponse
)
from app.schemas.tenant import TenantResponse
from app.schemas.company import CompanyResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse, summary="Autenticação de Usuário (Login)")
def login(
    login_data: LoginRequest,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Autentica um usuário por e-mail e senha, retornando os tokens JWT de Acesso e Refresh.
    """
    user = db.scalar(select(User).where(User.email == login_data.email))
    if not user or not security.verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta de usuário inativa"
        )

    # Generate JWT tokens
    access_token = security.create_access_token(subject=user.id)
    refresh_token_jwt = security.create_refresh_token(subject=user.id)

    # Store refresh token in database
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db_refresh_token = RefreshToken(
        user_id=user.id,
        token=refresh_token_jwt,
        expires_at=expires_at,
        revoked=False
    )
    db.add(db_refresh_token)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_jwt,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse, summary="Renovação de Token de Acesso")
def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Gera um novo token de acesso usando um refresh token válido e não revogado.
    """
    try:
        payload = security.decode_token(refresh_data.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token inválido")
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Refresh token inválido ou expirado")

    # Check refresh token status in DB
    stored_token = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token == refresh_data.refresh_token,
            RefreshToken.revoked == False
        )
    )
    if not stored_token:
        raise HTTPException(status_code=401, detail="Refresh token revogado ou inexistente")

    new_access_token = security.create_access_token(subject=user_id)
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=refresh_data.refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout", summary="Revogação de Refresh Token (Logout)")
def logout(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Revoga o refresh token fornecido para encerrar a sessão.
    """
    stored_token = db.scalar(
        select(RefreshToken).where(RefreshToken.token == refresh_data.refresh_token)
    )
    if stored_token:
        stored_token.revoked = True
        db.commit()
    return {"detail": "Sessão encerrada com sucesso"}


@router.get("/me", response_model=UserMeResponse, summary="Perfil do Usuário Autenticado")
def get_me(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Retorna o perfil do usuário atual, tenant, empresas acessíveis e permissões concedidas.
    """
    tenant = db.scalar(select(Tenant).where(Tenant.id == current_user.tenant_id))
    companies = db.scalars(
        select(Company).where(Company.tenant_id == current_user.tenant_id, Company.is_active == True)
    ).all()
    permissions = deps.get_user_permissions(db, current_user)

    return UserMeResponse(
        id=current_user.id,
        tenant_id=current_user.tenant_id,
        name=current_user.name,
        email=current_user.email,
        is_superuser=current_user.is_superuser,
        tenant=TenantResponse.model_validate(tenant),
        companies=[CompanyResponse.model_validate(c) for c in companies],
        permissions=permissions
    )
