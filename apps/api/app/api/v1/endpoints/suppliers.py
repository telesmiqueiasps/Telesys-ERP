from typing import List, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.api import deps
from app.models.user import User
from app.models.customer import Supplier
from app.schemas.supplier import (
    SupplierCreate,
    SupplierResponse,
    SupplierUpdate
)

router = APIRouter()


@router.get("/", response_model=List[SupplierResponse], summary="Listar Fornecedores")
def list_suppliers(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    company_id: Optional[UUID] = Query(None, description="Filtrar por Empresa"),
    search: Optional[str] = Query(None, description="Busca por Razão Social, CNPJ, email ou telefone"),
    is_active: Optional[bool] = Query(None, description="Filtrar por status ativo/inativo"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> Any:
    """
    Lista fornecedores do Tenant com busca por Razão Social, Nome Fantasia, CNPJ, email ou telefone.
    """
    target_company_id = company_id or current_user.company_id

    query = select(Supplier).where(
        Supplier.tenant_id == current_user.tenant_id,
        Supplier.company_id == target_company_id
    )

    if is_active is not None:
        query = query.where(Supplier.is_active == is_active)

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                Supplier.name.ilike(search_pattern),
                Supplier.trade_name.ilike(search_pattern),
                Supplier.document.ilike(search_pattern),
                Supplier.email.ilike(search_pattern),
                Supplier.phone.ilike(search_pattern),
                Supplier.contact_person.ilike(search_pattern)
            )
        )

    query = query.order_by(Supplier.name.asc()).offset(skip).limit(limit)
    suppliers = db.scalars(query).all()
    return suppliers


@router.post("/", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED, summary="Cadastrar Fornecedor")
def create_supplier(
    supplier_in: SupplierCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Cadastra um novo fornecedor para a empresa.
    """
    tenant_id = supplier_in.tenant_id or current_user.tenant_id
    company_id = supplier_in.company_id or current_user.company_id

    supplier = Supplier(
        **supplier_in.model_dump(exclude={"tenant_id", "company_id"}),
        tenant_id=tenant_id,
        company_id=company_id
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("/{supplier_id}", response_model=SupplierResponse, summary="Obter Detalhes do Fornecedor")
def get_supplier(
    supplier_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Retorna os detalhes de um fornecedor específico.
    """
    supplier = db.scalar(
        select(Supplier).where(
            Supplier.id == supplier_id,
            Supplier.tenant_id == current_user.tenant_id
        )
    )
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fornecedor não encontrado."
        )
    return supplier


@router.put("/{supplier_id}", response_model=SupplierResponse, summary="Atualizar Fornecedor")
def update_supplier(
    supplier_id: UUID,
    supplier_in: SupplierUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Atualiza os dados de um fornecedor existente.
    """
    supplier = db.scalar(
        select(Supplier).where(
            Supplier.id == supplier_id,
            Supplier.tenant_id == current_user.tenant_id
        )
    )
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fornecedor não encontrado."
        )

    update_data = supplier_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)

    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.delete("/{supplier_id}", response_model=SupplierResponse, summary="Inativar/Excluir Fornecedor")
def delete_supplier(
    supplier_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Inativa (soft-delete) o cadastro do fornecedor.
    """
    supplier = db.scalar(
        select(Supplier).where(
            Supplier.id == supplier_id,
            Supplier.tenant_id == current_user.tenant_id
        )
    )
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fornecedor não encontrado."
        )

    supplier.is_active = False
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier
