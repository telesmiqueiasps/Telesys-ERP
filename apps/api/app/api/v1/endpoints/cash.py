from typing import List, Any, Optional
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, desc

from app.api import deps
from app.models.user import User
from app.models.cash import (
    CashRegister,
    CashMovement,
    CashRegisterStatus,
    CashMovementType,
    PaymentMethod,
)
from app.schemas.cash import (
    CashRegisterOpenInput,
    CashRegisterCloseInput,
    CashRegisterResponse,
    CashRegisterDetailResponse,
    CashMovementCreate,
    CashMovementResponse,
)

router = APIRouter()


@router.get("/current", response_model=Optional[CashRegisterDetailResponse], summary="Obter Caixa Aberto Atual")
def get_current_cash(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    company_id: Optional[UUID] = Query(None, description="Filtrar por Empresa"),
) -> Any:
    """
    Retorna a sessão de caixa atualmente aberta para o operador/empresa.
    """
    target_company_id = company_id or current_user.company_id

    register = db.scalar(
        select(CashRegister)
        .options(joinedload(CashRegister.movements), joinedload(CashRegister.user))
        .where(
            CashRegister.tenant_id == current_user.tenant_id,
            CashRegister.company_id == target_company_id,
            CashRegister.user_id == current_user.id,
            CashRegister.status == CashRegisterStatus.OPEN,
        )
    )

    if not register:
        return None

    response = CashRegisterDetailResponse.model_validate(register)
    if register.user:
        response.user_name = register.user.name
    return response


@router.post("/open", response_model=CashRegisterDetailResponse, status_code=status.HTTP_201_CREATED, summary="Abrir Sessão de Caixa")
def open_cash_register(
    input_data: CashRegisterOpenInput,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    company_id: Optional[UUID] = Query(None, description="Empresa do Caixa"),
) -> Any:
    """
    Abre uma nova sessão de caixa para o operador com o fundo de troco inicial.
    """
    target_company_id = company_id or current_user.company_id

    # Verifica se já existe caixa aberto para o operador nesta empresa
    existing = db.scalar(
        select(CashRegister).where(
            CashRegister.tenant_id == current_user.tenant_id,
            CashRegister.company_id == target_company_id,
            CashRegister.user_id == current_user.id,
            CashRegister.status == CashRegisterStatus.OPEN,
        )
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe uma sessão de caixa aberta para este operador nesta empresa."
        )

    initial_bal = input_data.initial_balance or 0

    register = CashRegister(
        tenant_id=current_user.tenant_id,
        company_id=target_company_id,
        user_id=current_user.id,
        opened_at=datetime.utcnow(),
        initial_balance=initial_bal,
        current_balance=initial_bal,
        status=CashRegisterStatus.OPEN,
        notes=input_data.notes,
    )
    db.add(register)
    db.flush()

    # Registra a movimentação inicial de abertura
    opening_mov = CashMovement(
        cash_register_id=register.id,
        tenant_id=current_user.tenant_id,
        company_id=target_company_id,
        user_id=current_user.id,
        movement_type=CashMovementType.OPENING,
        payment_method=PaymentMethod.MONEY,
        amount=initial_bal,
        description="Fundo de Troco (Abertura de Caixa)",
    )
    db.add(opening_mov)

    db.commit()
    db.refresh(register)

    # Reload with relationships
    register = db.scalar(
        select(CashRegister)
        .options(joinedload(CashRegister.movements), joinedload(CashRegister.user))
        .where(CashRegister.id == register.id)
    )

    response = CashRegisterDetailResponse.model_validate(register)
    if register and register.user:
        response.user_name = register.user.name
    return response


@router.post("/movements", response_model=CashMovementResponse, status_code=status.HTTP_201_CREATED, summary="Registrar Movimentação de Caixa (Suprimento/Sangria)")
def create_cash_movement(
    input_data: CashMovementCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    company_id: Optional[UUID] = Query(None, description="Empresa do Caixa"),
) -> Any:
    """
    Registra uma entrada manual de dinheiro (Suprimento) ou retirada manual (Sangria) no caixa aberto.
    """
    target_company_id = company_id or current_user.company_id

    register = db.scalar(
        select(CashRegister).where(
            CashRegister.tenant_id == current_user.tenant_id,
            CashRegister.company_id == target_company_id,
            CashRegister.user_id == current_user.id,
            CashRegister.status == CashRegisterStatus.OPEN,
        )
    )

    if not register:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Não há caixa aberto no momento para realizar movimentações."
        )

    if input_data.movement_type not in [CashMovementType.SUPPLY, CashMovementType.BLEED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de movimentação inválido. Utilize SUPPLY (Suprimento) ou BLEED (Sangria)."
        )

    if input_data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O valor da movimentação deve ser maior que zero."
        )

    # Atualiza o saldo do caixa
    if input_data.movement_type == CashMovementType.SUPPLY:
        register.current_balance += input_data.amount
    elif input_data.movement_type == CashMovementType.BLEED:
        if register.current_balance < input_data.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Saldo insuficiente no caixa para realizar sangria de R$ {input_data.amount:.2f}. Saldo atual em dinheiro: R$ {register.current_balance:.2f}."
            )
        register.current_balance -= input_data.amount

    movement = CashMovement(
        cash_register_id=register.id,
        tenant_id=current_user.tenant_id,
        company_id=target_company_id,
        user_id=current_user.id,
        movement_type=input_data.movement_type,
        payment_method=input_data.payment_method,
        amount=input_data.amount,
        description=input_data.description or ("Suprimento de Caixa" if input_data.movement_type == CashMovementType.SUPPLY else "Sangria de Caixa"),
    )
    db.add(movement)
    db.add(register)
    db.commit()
    db.refresh(movement)
    return movement


@router.post("/close", response_model=CashRegisterDetailResponse, summary="Fechar Sessão de Caixa")
def close_cash_register(
    input_data: CashRegisterCloseInput,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    company_id: Optional[UUID] = Query(None, description="Empresa do Caixa"),
) -> Any:
    """
    Realiza o fechamento do caixa aberto, apurando a diferença entre o saldo apurado e o valor declarado.
    """
    target_company_id = company_id or current_user.company_id

    register = db.scalar(
        select(CashRegister)
        .options(joinedload(CashRegister.movements))
        .where(
            CashRegister.tenant_id == current_user.tenant_id,
            CashRegister.company_id == target_company_id,
            CashRegister.user_id == current_user.id,
            CashRegister.status == CashRegisterStatus.OPEN,
        )
    )

    if not register:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma sessão de caixa aberta encontrada para ser fechada."
        )

    # Apura a divergência (Valor Declarado pelo Operador - Saldo Calculado do Sistema)
    diff = input_data.final_declared_balance - register.current_balance

    register.status = CashRegisterStatus.CLOSED
    register.closed_at = datetime.utcnow()
    register.final_declared_balance = input_data.final_declared_balance
    register.difference_amount = diff
    if input_data.notes:
        register.notes = f"{register.notes or ''}\n[Fechamento]: {input_data.notes}".strip()

    # Registra movimentação de fechamento
    closing_mov = CashMovement(
        cash_register_id=register.id,
        tenant_id=current_user.tenant_id,
        company_id=target_company_id,
        user_id=current_user.id,
        movement_type=CashMovementType.CLOSING,
        payment_method=PaymentMethod.MONEY,
        amount=input_data.final_declared_balance,
        description=f"Fechamento de Caixa. Saldo Declarado: R$ {input_data.final_declared_balance:.2f} (Diferença: R$ {diff:.2f})",
    )
    db.add(closing_mov)
    db.add(register)
    db.commit()

    # Reload with full data
    register = db.scalar(
        select(CashRegister)
        .options(joinedload(CashRegister.movements), joinedload(CashRegister.user))
        .where(CashRegister.id == register.id)
    )

    response = CashRegisterDetailResponse.model_validate(register)
    if register and register.user:
        response.user_name = register.user.name
    return response


@router.get("/history", response_model=List[CashRegisterDetailResponse], summary="Histórico de Sessões de Caixa")
def list_cash_history(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    company_id: Optional[UUID] = Query(None, description="Filtrar por Empresa"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> Any:
    """
    Retorna o histórico de caixas encerrados da empresa.
    """
    target_company_id = company_id or current_user.company_id

    query = (
        select(CashRegister)
        .options(joinedload(CashRegister.movements), joinedload(CashRegister.user))
        .where(
            CashRegister.tenant_id == current_user.tenant_id,
            CashRegister.company_id == target_company_id,
        )
        .order_by(desc(CashRegister.opened_at))
        .offset(skip)
        .limit(limit)
    )

    registers = db.scalars(query).unique().all()
    results = []
    for reg in registers:
        detail = CashRegisterDetailResponse.model_validate(reg)
        if reg.user:
            detail.user_name = reg.user.name
        results.append(detail)
    return results
