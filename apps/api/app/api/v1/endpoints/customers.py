from typing import List, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.api import deps
from app.models.user import User
from app.models.customer import Customer
from app.schemas.customer import (
    CustomerCreate,
    CustomerResponse,
    CustomerUpdate
)

router = APIRouter()


@router.get("/", response_model=List[CustomerResponse], summary="Listar Clientes")
def list_customers(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    company_id: Optional[UUID] = Query(None, description="Filtrar por Empresa"),
    search: Optional[str] = Query(None, description="Busca por nome, CPF/CNPJ, email ou telefone"),
    is_active: Optional[bool] = Query(None, description="Filtrar por status ativo/inativo"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> Any:
    """
    Lista clientes do Tenant com suporte a busca rápida por nome, CPF/CNPJ, email ou telefone.
    """
    target_company_id = company_id or current_user.company_id

    query = select(Customer).where(
        Customer.tenant_id == current_user.tenant_id,
        Customer.company_id == target_company_id
    )

    if is_active is not None:
        query = query.where(Customer.is_active == is_active)

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                Customer.name.ilike(search_pattern),
                Customer.trade_name.ilike(search_pattern),
                Customer.document.ilike(search_pattern),
                Customer.email.ilike(search_pattern),
                Customer.phone.ilike(search_pattern)
            )
        )

    query = query.order_by(Customer.name.asc()).offset(skip).limit(limit)
    customers = db.scalars(query).all()
    return customers


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED, summary="Cadastrar Cliente")
def create_customer(
    customer_in: CustomerCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Cadastra um novo cliente para a empresa.
    """
    tenant_id = customer_in.tenant_id or current_user.tenant_id
    company_id = customer_in.company_id or current_user.company_id

    customer = Customer(
        **customer_in.model_dump(exclude={"tenant_id", "company_id"}),
        tenant_id=tenant_id,
        company_id=company_id
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerResponse, summary="Obter Detalhes do Cliente")
def get_customer(
    customer_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Retorna os detalhes de um cliente específico.
    """
    customer = db.scalar(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.tenant_id == current_user.tenant_id
        )
    )
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado."
        )
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse, summary="Atualizar Cliente")
def update_customer(
    customer_id: UUID,
    customer_in: CustomerUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Atualiza os dados de um cliente existente.
    """
    customer = db.scalar(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.tenant_id == current_user.tenant_id
        )
    )
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado."
        )

    update_data = customer_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)

    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}", response_model=CustomerResponse, summary="Inativar/Excluir Cliente")
def delete_customer(
    customer_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Inativa (soft-delete) o cadastro do cliente.
    """
    customer = db.scalar(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.tenant_id == current_user.tenant_id
        )
    )
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado."
        )

    customer.is_active = False
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer
