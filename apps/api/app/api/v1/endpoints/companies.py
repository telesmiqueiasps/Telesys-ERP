from typing import List, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api import deps
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate

router = APIRouter()


@router.get("", response_model=List[CompanyResponse], summary="Listar Empresas do Tenant")
def list_companies(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Lista todas as empresas pertencentes ao Tenant do usuário atual.
    """
    companies = db.scalars(
        select(Company).where(Company.tenant_id == current_user.tenant_id)
    ).all()
    return companies


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED, summary="Criar Empresa")
def create_company(
    company_in: CompanyCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("usuarios.gerenciar"))
) -> Any:
    """
    Cria uma nova empresa vinculada ao Tenant.
    """
    if not current_user.is_superuser and company_in.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Não é permitido criar empresas em outro tenant")

    company = Company(
        tenant_id=company_in.tenant_id,
        name=company_in.name,
        trade_name=company_in.trade_name,
        cnpj=company_in.cnpj,
        state_registration=company_in.state_registration,
        is_active=company_in.is_active
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("/{company_id}", response_model=CompanyResponse, summary="Obter Empresa por ID")
def get_company(
    company_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Obtém detalhes de uma empresa.
    """
    company = db.scalar(select(Company).where(Company.id == company_id))
    if not company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    if not current_user.is_superuser and company.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acesso não autorizado a esta empresa")

    return company
