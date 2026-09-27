import uuid
from typing import List, Any
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, desc, func, or_

from app.api import deps
from app.models.user import User
from app.models.company import Company
from app.models.customer import Customer, Supplier
from app.models.finance import (
    FinancialCategory,
    FinancialCategoryType,
    AccountPayable,
    AccountPayableStatus,
    AccountReceivable,
    AccountReceivableStatus,
    FinancialMovement,
)
from app.schemas.finance import (
    FinancialCategoryCreate,
    FinancialCategoryResponse,
    AccountPayableCreate,
    AccountPayablePayInput,
    AccountPayableResponse,
    AccountReceivableCreate,
    AccountReceivableReceiveInput,
    AccountReceivableResponse,
    FinancialMovementResponse,
    FinancialSummaryResponse,
)

router = APIRouter()


# --- Categorias Financeiras ---
@router.get("/categories", response_model=List[FinancialCategoryResponse], summary="Listar Categorias Financeiras")
def list_categories(
    company_id: uuid.UUID = Query(..., description="ID da empresa/filial"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    stmt = (
        select(FinancialCategory)
        .where(
            FinancialCategory.company_id == company_id,
            FinancialCategory.tenant_id == current_user.tenant_id
        )
        .order_by(FinancialCategory.name)
    )
    return db.scalars(stmt).all()


@router.post("/categories", response_model=FinancialCategoryResponse, status_code=status.HTTP_201_CREATED, summary="Criar Categoria Financeira")
def create_category(
    cat_in: FinancialCategoryCreate,
    company_id: uuid.UUID = Query(..., description="ID da empresa/filial"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    cat = FinancialCategory(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        company_id=company_id,
        name=cat_in.name,
        type=cat_in.type,
        color=cat_in.color,
        is_active=cat_in.is_active,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


# --- Contas a Pagar ---
@router.get("/payables", response_model=List[AccountPayableResponse], summary="Listar Contas a Pagar")
def list_payables(
    company_id: uuid.UUID = Query(..., description="ID da empresa"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    today = date.today()
    stmt = (
        select(AccountPayable)
        .options(
            selectinload(AccountPayable.supplier),
            selectinload(AccountPayable.category)
        )
        .where(
            AccountPayable.company_id == company_id,
            AccountPayable.tenant_id == current_user.tenant_id
        )
        .order_by(AccountPayable.due_date)
    )
    payables = db.scalars(stmt).all()

    # Atualizar status vencido em tempo real
    result = []
    for p in payables:
        if p.status == AccountPayableStatus.PENDING.value and p.due_date < today:
            p.status = AccountPayableStatus.OVERDUE.value
            db.add(p)

        result.append(
            AccountPayableResponse(
                id=p.id,
                tenant_id=p.tenant_id,
                company_id=p.company_id,
                supplier_id=p.supplier_id,
                supplier_name=p.supplier.name if p.supplier else None,
                category_id=p.category_id,
                category_name=p.category.name if p.category else None,
                purchase_id=p.purchase_id,
                description=p.description,
                amount=float(p.amount),
                paid_amount=float(p.paid_amount),
                due_date=p.due_date,
                paid_at=p.paid_at,
                status=p.status,
                payment_method=p.payment_method,
                notes=p.notes,
                created_at=p.created_at,
            )
        )
    db.commit()
    return result


@router.post("/payables", response_model=AccountPayableResponse, status_code=status.HTTP_201_CREATED, summary="Cadastrar Conta a Pagar")
def create_payable(
    pay_in: AccountPayableCreate,
    company_id: uuid.UUID = Query(..., description="ID da empresa"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    today = date.today()
    initial_status = AccountPayableStatus.OVERDUE.value if pay_in.due_date < today else AccountPayableStatus.PENDING.value

    payable = AccountPayable(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        company_id=company_id,
        supplier_id=pay_in.supplier_id,
        category_id=pay_in.category_id,
        purchase_id=pay_in.purchase_id,
        description=pay_in.description,
        amount=pay_in.amount,
        paid_amount=0.0,
        due_date=pay_in.due_date,
        status=initial_status,
        notes=pay_in.notes,
    )
    db.add(payable)
    db.commit()
    db.refresh(payable)

    supplier = db.scalar(select(Supplier).where(Supplier.id == payable.supplier_id)) if payable.supplier_id else None
    category = db.scalar(select(FinancialCategory).where(FinancialCategory.id == payable.category_id)) if payable.category_id else None

    return AccountPayableResponse(
        id=payable.id,
        tenant_id=payable.tenant_id,
        company_id=payable.company_id,
        supplier_id=payable.supplier_id,
        supplier_name=supplier.name if supplier else None,
        category_id=payable.category_id,
        category_name=category.name if category else None,
        purchase_id=payable.purchase_id,
        description=payable.description,
        amount=float(payable.amount),
        paid_amount=float(payable.paid_amount),
        due_date=payable.due_date,
        paid_at=payable.paid_at,
        status=payable.status,
        payment_method=payable.payment_method,
        notes=payable.notes,
        created_at=payable.created_at,
    )


@router.post("/payables/{payable_id}/pay", response_model=AccountPayableResponse, summary="Baixar / Liquidar Conta a Pagar")
def pay_account_payable(
    payable_id: uuid.UUID,
    pay_data: AccountPayablePayInput,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    payable = db.scalar(
        select(AccountPayable)
        .options(
            selectinload(AccountPayable.supplier),
            selectinload(AccountPayable.category)
        )
        .where(
            AccountPayable.id == payable_id,
            AccountPayable.tenant_id == current_user.tenant_id
        )
    )
    if not payable:
        raise HTTPException(status_code=404, detail="Conta a pagar não encontrada.")

    payable.paid_amount = float(payable.paid_amount) + pay_data.paid_amount
    payable.paid_at = pay_data.paid_at or datetime.now()
    payable.payment_method = pay_data.payment_method

    if payable.paid_amount >= float(payable.amount):
        payable.status = AccountPayableStatus.PAID.value

    # Gerar extrato de fluxo de caixa (SAIDA)
    movement = FinancialMovement(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        company_id=payable.company_id,
        user_id=current_user.id,
        category_id=payable.category_id,
        movement_type="SAIDA",
        amount=pay_data.paid_amount,
        description=f"Pagamento: {payable.description}",
        reference_type="PAYABLE",
        reference_id=payable.id,
    )
    db.add(movement)
    db.commit()
    db.refresh(payable)

    return AccountPayableResponse(
        id=payable.id,
        tenant_id=payable.tenant_id,
        company_id=payable.company_id,
        supplier_id=payable.supplier_id,
        supplier_name=payable.supplier.name if payable.supplier else None,
        category_id=payable.category_id,
        category_name=payable.category.name if payable.category else None,
        purchase_id=payable.purchase_id,
        description=payable.description,
        amount=float(payable.amount),
        paid_amount=float(payable.paid_amount),
        due_date=payable.due_date,
        paid_at=payable.paid_at,
        status=payable.status,
        payment_method=payable.payment_method,
        notes=payable.notes,
        created_at=payable.created_at,
    )


# --- Contas a Receber ---
@router.get("/receivables", response_model=List[AccountReceivableResponse], summary="Listar Contas a Receber")
def list_receivables(
    company_id: uuid.UUID = Query(..., description="ID da empresa"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    today = date.today()
    stmt = (
        select(AccountReceivable)
        .options(
            selectinload(AccountReceivable.customer),
            selectinload(AccountReceivable.category)
        )
        .where(
            AccountReceivable.company_id == company_id,
            AccountReceivable.tenant_id == current_user.tenant_id
        )
        .order_by(AccountReceivable.due_date)
    )
    receivables = db.scalars(stmt).all()

    result = []
    for r in receivables:
        if r.status == AccountReceivableStatus.PENDING.value and r.due_date < today:
            r.status = AccountReceivableStatus.OVERDUE.value
            db.add(r)

        result.append(
            AccountReceivableResponse(
                id=r.id,
                tenant_id=r.tenant_id,
                company_id=r.company_id,
                customer_id=r.customer_id,
                customer_name=r.customer.name if r.customer else None,
                category_id=r.category_id,
                category_name=r.category.name if r.category else None,
                sale_id=r.sale_id,
                description=r.description,
                amount=float(r.amount),
                received_amount=float(r.received_amount),
                due_date=r.due_date,
                received_at=r.received_at,
                status=r.status,
                payment_method=r.payment_method,
                notes=r.notes,
                created_at=r.created_at,
            )
        )
    db.commit()
    return result


@router.post("/receivables", response_model=AccountReceivableResponse, status_code=status.HTTP_201_CREATED, summary="Cadastrar Conta a Receber")
def create_receivable(
    rec_in: AccountReceivableCreate,
    company_id: uuid.UUID = Query(..., description="ID da empresa"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    today = date.today()
    initial_status = AccountReceivableStatus.OVERDUE.value if rec_in.due_date < today else AccountReceivableStatus.PENDING.value

    receivable = AccountReceivable(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        company_id=company_id,
        customer_id=rec_in.customer_id,
        category_id=rec_in.category_id,
        sale_id=rec_in.sale_id,
        description=rec_in.description,
        amount=rec_in.amount,
        received_amount=0.0,
        due_date=rec_in.due_date,
        status=initial_status,
        notes=rec_in.notes,
    )
    db.add(receivable)
    db.commit()
    db.refresh(receivable)

    customer = db.scalar(select(Customer).where(Customer.id == receivable.customer_id)) if receivable.customer_id else None
    category = db.scalar(select(FinancialCategory).where(FinancialCategory.id == receivable.category_id)) if receivable.category_id else None

    return AccountReceivableResponse(
        id=receivable.id,
        tenant_id=receivable.tenant_id,
        company_id=receivable.company_id,
        customer_id=receivable.customer_id,
        customer_name=customer.name if customer else None,
        category_id=receivable.category_id,
        category_name=category.name if category else None,
        sale_id=receivable.sale_id,
        description=receivable.description,
        amount=float(receivable.amount),
        received_amount=float(receivable.received_amount),
        due_date=receivable.due_date,
        received_at=receivable.received_at,
        status=receivable.status,
        payment_method=receivable.payment_method,
        notes=receivable.notes,
        created_at=receivable.created_at,
    )


@router.post("/receivables/{receivable_id}/receive", response_model=AccountReceivableResponse, summary="Baixar / Liquidar Conta a Receber")
def receive_account_receivable(
    receivable_id: uuid.UUID,
    rec_data: AccountReceivableReceiveInput,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    receivable = db.scalar(
        select(AccountReceivable)
        .options(
            selectinload(AccountReceivable.customer),
            selectinload(AccountReceivable.category)
        )
        .where(
            AccountReceivable.id == receivable_id,
            AccountReceivable.tenant_id == current_user.tenant_id
        )
    )
    if not receivable:
        raise HTTPException(status_code=404, detail="Conta a receber não encontrada.")

    receivable.received_amount = float(receivable.received_amount) + rec_data.received_amount
    receivable.received_at = rec_data.received_at or datetime.now()
    receivable.payment_method = rec_data.payment_method

    if receivable.received_amount >= float(receivable.amount):
        receivable.status = AccountReceivableStatus.RECEIVED.value

    # Gerar extrato de fluxo de caixa (ENTRADA)
    movement = FinancialMovement(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        company_id=receivable.company_id,
        user_id=current_user.id,
        category_id=receivable.category_id,
        movement_type="ENTRADA",
        amount=rec_data.received_amount,
        description=f"Recebimento: {receivable.description}",
        reference_type="RECEIVABLE",
        reference_id=receivable.id,
    )
    db.add(movement)
    db.commit()
    db.refresh(receivable)

    return AccountReceivableResponse(
        id=receivable.id,
        tenant_id=receivable.tenant_id,
        company_id=receivable.company_id,
        customer_id=receivable.customer_id,
        customer_name=receivable.customer.name if receivable.customer else None,
        category_id=receivable.category_id,
        category_name=receivable.category.name if receivable.category else None,
        sale_id=receivable.sale_id,
        description=receivable.description,
        amount=float(receivable.amount),
        received_amount=float(receivable.received_amount),
        due_date=receivable.due_date,
        received_at=receivable.received_at,
        status=receivable.status,
        payment_method=receivable.payment_method,
        notes=receivable.notes,
        created_at=receivable.created_at,
    )


# --- Resumo / Dashboard Financeiro ---
@router.get("/summary", response_model=FinancialSummaryResponse, summary="Resumo dos Indicadores Financeiros")
def get_financial_summary(
    company_id: uuid.UUID = Query(..., description="ID da empresa"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    today = date.today()

    # Contas a Pagar Pendentes
    payables_pending = db.scalar(
        select(func.coalesce(func.sum(AccountPayable.amount - AccountPayable.paid_amount), 0.0)).where(
            AccountPayable.company_id == company_id,
            AccountPayable.tenant_id == current_user.tenant_id,
            AccountPayable.status.in_([AccountPayableStatus.PENDING.value, AccountPayableStatus.OVERDUE.value])
        )
    )

    # Contas a Receber Pendentes
    receivables_pending = db.scalar(
        select(func.coalesce(func.sum(AccountReceivable.amount - AccountReceivable.received_amount), 0.0)).where(
            AccountReceivable.company_id == company_id,
            AccountReceivable.tenant_id == current_user.tenant_id,
            AccountReceivable.status.in_([AccountReceivableStatus.PENDING.value, AccountReceivableStatus.OVERDUE.value])
        )
    )

    # Contas Vencidas (Pagar + Receber)
    payables_overdue = db.scalar(
        select(func.coalesce(func.sum(AccountPayable.amount - AccountPayable.paid_amount), 0.0)).where(
            AccountPayable.company_id == company_id,
            AccountPayable.tenant_id == current_user.tenant_id,
            AccountPayable.due_date < today,
            AccountPayable.status != AccountPayableStatus.PAID.value
        )
    )

    forecast_balance = float(receivables_pending) - float(payables_pending)

    return FinancialSummaryResponse(
        total_receivable_pending=float(receivables_pending),
        total_payable_pending=float(payables_pending),
        total_overdue=float(payables_overdue),
        forecast_balance=float(forecast_balance),
    )
