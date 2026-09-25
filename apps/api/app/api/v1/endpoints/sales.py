from typing import List, Any, Optional
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, desc, func

from app.api import deps
from app.models.user import User
from app.models.product import Product
from app.models.customer import Customer
from app.models.cash import CashRegister, CashMovement, CashRegisterStatus, CashMovementType, PaymentMethod
from app.models.stock import StockMovement, StockMovementType
from app.models.sale import Sale, SaleItem, SalePayment, SaleStatus
from app.schemas.sale import (
    SaleCreate,
    SaleResponse,
    SaleDetailResponse,
)

router = APIRouter()


@router.post("/", response_model=SaleDetailResponse, status_code=status.HTTP_201_CREATED, summary="Finalizar Venda no PDV")
def create_sale(
    sale_in: SaleCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    company_id: Optional[UUID] = Query(None, description="Empresa da Venda"),
) -> Any:
    """
    Registra e finaliza uma nova venda no PDV:
    - Valida sessão de caixa aberta do operador.
    - Baixa o estoque dos produtos e gera o histórico de movimentações (OUT/SALE).
    - Lança a entrada de pagamento no caixa do operador.
    """
    target_company_id = company_id or current_user.company_id

    # 1. Verifica se há caixa aberto para o operador
    cash_register = db.scalar(
        select(CashRegister).where(
            CashRegister.tenant_id == current_user.tenant_id,
            CashRegister.company_id == target_company_id,
            CashRegister.user_id == current_user.id,
            CashRegister.status == CashRegisterStatus.OPEN,
        )
    )

    if not cash_register:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não há uma sessão de caixa aberta para este operador. Abra o caixa antes de realizar vendas."
        )

    if not sale_in.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O carrinho de vendas não pode estar vazio."
        )

    if not sale_in.payments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe ao menos uma forma de pagamento para finalizar a venda."
        )

    # 2. Gera código único de venda VND-XXXXXX
    count = db.scalar(
        select(func.count(Sale.id)).where(
            Sale.tenant_id == current_user.tenant_id,
            Sale.company_id == target_company_id
        )
    ) or 0
    sale_code = f"VND-{(count + 1):06d}"

    # 3. Processa Itens e Cálculos
    subtotal = Decimal("0.00")
    sale_items_to_create = []
    stock_movements_to_create = []

    for idx, item_in in enumerate(sale_in.items, start=1):
        product = db.scalar(
            select(Product).where(
                Product.id == item_in.product_id,
                Product.tenant_id == current_user.tenant_id,
                Product.company_id == target_company_id
            )
        )
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produto com ID {item_in.product_id} não encontrado."
            )

        item_subtotal = item_in.quantity * item_in.unit_price
        item_total = item_subtotal - item_in.discount_amount
        subtotal += item_subtotal

        # Baixa estoque do produto
        product.stock_qty -= item_in.quantity
        db.add(product)

        # Histórico de estoque
        stock_mov = StockMovement(
            tenant_id=current_user.tenant_id,
            company_id=target_company_id,
            product_id=product.id,
            user_id=current_user.id,
            movement_type=StockMovementType.OUT,
            quantity=item_in.quantity,
            unit_price=item_in.unit_price,
            total_price=item_total,
            description=f"Venda PDV {sale_code}",
        )
        stock_movements_to_create.append(stock_mov)

        # Item da Venda
        sale_item = SaleItem(
            item_number=idx,
            product_id=product.id,
            product_name=product.name,
            unit_code=product.unit.code if product.unit else "UN",
            quantity=item_in.quantity,
            unit_price=item_in.unit_price,
            discount_amount=item_in.discount_amount,
            total_price=item_total,
            ncm=product.ncm,
            cest=product.cest,
        )
        sale_items_to_create.append(sale_item)

    total_amount = subtotal - sale_in.discount_amount
    if total_amount < Decimal("0.00"):
        total_amount = Decimal("0.00")

    # 4. Cria a Venda
    sale = Sale(
        tenant_id=current_user.tenant_id,
        company_id=target_company_id,
        cash_register_id=cash_register.id,
        customer_id=sale_in.customer_id,
        user_id=current_user.id,
        code=sale_code,
        status=SaleStatus.COMPLETED,
        subtotal=subtotal,
        discount_amount=sale_in.discount_amount,
        total_amount=total_amount,
        notes=sale_in.notes,
        items=sale_items_to_create,
    )
    db.add(sale)
    db.flush()

    # Adiciona movimentações de estoque
    for sm in stock_movements_to_create:
        db.add(sm)

    # 5. Processa Pagamentos e atualiza o Saldo do Caixa
    for p_in in sale_in.payments:
        payment = SalePayment(
            sale_id=sale.id,
            payment_method=p_in.payment_method,
            amount=p_in.amount,
            change_amount=p_in.change_amount,
        )
        db.add(payment)

        # Se for pagamento em dinheiro, incrementa o caixa em dinheiro
        pm_enum = PaymentMethod.MONEY if p_in.payment_method == "MONEY" else PaymentMethod.OTHER
        if p_in.payment_method == "MONEY":
            net_cash_received = p_in.amount - p_in.change_amount
            if net_cash_received > 0:
                cash_register.current_balance += net_cash_received
                db.add(cash_register)

        # Registra movimentação de caixa correspondente
        cash_mov = CashMovement(
            cash_register_id=cash_register.id,
            tenant_id=current_user.tenant_id,
            company_id=target_company_id,
            user_id=current_user.id,
            movement_type=CashMovementType.SALE,
            payment_method=pm_enum,
            amount=p_in.amount,
            description=f"Venda PDV {sale_code}",
        )
        db.add(cash_mov)

    db.commit()

    # Reload sale with all relationships
    sale = db.scalar(
        select(Sale)
        .options(
            joinedload(Sale.items),
            joinedload(Sale.payments),
            joinedload(Sale.customer),
            joinedload(Sale.user),
        )
        .where(Sale.id == sale.id)
    )

    response = SaleDetailResponse.model_validate(sale)
    if sale and sale.customer:
        response.customer_name = sale.customer.name
    if sale and sale.user:
        response.user_name = sale.user.name

    return response


@router.get("/", response_model=List[SaleDetailResponse], summary="Listar Vendas Realizadas")
def list_sales(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    company_id: Optional[UUID] = Query(None, description="Filtrar por Empresa"),
    status_filter: Optional[SaleStatus] = Query(None, description="Filtrar por status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> Any:
    """
    Retorna o histórico de vendas realizadas na empresa.
    """
    target_company_id = company_id or current_user.company_id

    query = (
        select(Sale)
        .options(
            joinedload(Sale.items),
            joinedload(Sale.payments),
            joinedload(Sale.customer),
            joinedload(Sale.user),
        )
        .where(
            Sale.tenant_id == current_user.tenant_id,
            Sale.company_id == target_company_id,
        )
    )

    if status_filter:
        query = query.where(Sale.status == status_filter)

    query = query.order_by(desc(Sale.created_at)).offset(skip).limit(limit)

    sales = db.scalars(query).unique().all()
    results = []
    for s in sales:
        detail = SaleDetailResponse.model_validate(s)
        if s.customer:
            detail.customer_name = s.customer.name
        if s.user:
            detail.user_name = s.user.name
        results.append(detail)

    return results


@router.get("/{sale_id}", response_model=SaleDetailResponse, summary="Obter Detalhes da Venda")
def get_sale_detail(
    sale_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retorna os detalhes completos de uma venda específica.
    """
    sale = db.scalar(
        select(Sale)
        .options(
            joinedload(Sale.items),
            joinedload(Sale.payments),
            joinedload(Sale.customer),
            joinedload(Sale.user),
        )
        .where(
            Sale.id == sale_id,
            Sale.tenant_id == current_user.tenant_id,
        )
    )

    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venda não encontrada."
        )

    response = SaleDetailResponse.model_validate(sale)
    if sale.customer:
        response.customer_name = sale.customer.name
    if sale.user:
        response.user_name = sale.user.name

    return response
