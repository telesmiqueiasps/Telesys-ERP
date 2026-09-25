from typing import List, Any, Optional
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api import deps
from app.models.user import User
from app.models.product import Product
from app.models.stock import StockMovement, StockMovementType
from app.schemas.stock import StockMovementCreate, StockMovementDetailResponse

router = APIRouter()


@router.get("/movements", response_model=List[StockMovementDetailResponse], summary="Listar Histórico de Movimentações de Estoque")
def list_stock_movements(
    company_id: Optional[UUID] = Query(None, description="Filtrar por ID da empresa"),
    product_id: Optional[UUID] = Query(None, description="Filtrar por produto"),
    movement_type: Optional[str] = Query(None, description="Filtrar por tipo de movimentação"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("estoque.visualizar"))
) -> Any:
    """
    Lista o histórico auditável de movimentações de estoque (Append-Only).
    """
    stmt = select(StockMovement).where(StockMovement.tenant_id == current_user.tenant_id)

    if company_id:
        stmt = stmt.where(StockMovement.company_id == company_id)

    if product_id:
        stmt = stmt.where(StockMovement.product_id == product_id)

    if movement_type:
        stmt = stmt.where(StockMovement.movement_type == movement_type)

    stmt = stmt.order_by(StockMovement.created_at.desc()).offset(skip).limit(limit)

    movements = db.scalars(stmt).all()
    return movements


@router.post("/movements", response_model=StockMovementDetailResponse, status_code=status.HTTP_201_CREATED, summary="Registrar Movimentação de Estoque")
def create_stock_movement(
    movement_in: StockMovementCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("estoque.ajuste"))
) -> Any:
    """
    Registra uma nova movimentação de estoque de forma transacional e atualiza o saldo cacheado do produto.
    """
    product = db.scalar(
        select(Product).where(
            Product.id == movement_in.product_id,
            Product.tenant_id == current_user.tenant_id
        )
    )
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    previous_qty = Decimal(str(product.stock_qty))
    movement_qty = Decimal(str(movement_in.quantity))

    # Determine direction based on movement_type
    m_type = movement_in.movement_type.upper()
    if m_type in ["ENTRADA_NF", "AJUSTE_ENTRADA"]:
        new_qty = previous_qty + abs(movement_qty)
        qty_to_store = abs(movement_qty)
    elif m_type in ["SAIDA_VENDA", "AJUSTE_SAIDA"]:
        new_qty = previous_qty - abs(movement_qty)
        qty_to_store = -abs(movement_qty)
    elif m_type == "ESTORNO":
        new_qty = previous_qty + movement_qty
        qty_to_store = movement_qty
    else:
        raise HTTPException(status_code=400, detail=f"Tipo de movimentação inválido: {movement_in.movement_type}")

    # Prevent negative stock if needed or allow with audit log
    if new_qty < 0:
        raise HTTPException(status_code=400, detail=f"Saldo insuficiente em estoque. Saldo atual: {previous_qty}")

    # 1. Append-only movement log
    movement = StockMovement(
        tenant_id=current_user.tenant_id,
        company_id=movement_in.company_id,
        product_id=movement_in.product_id,
        user_id=current_user.id,
        movement_type=m_type,
        quantity=float(qty_to_store),
        previous_qty=float(previous_qty),
        new_qty=float(new_qty),
        unit_cost=float(movement_in.unit_cost) if movement_in.unit_cost else None,
        reference_doc=movement_in.reference_doc,
        notes=movement_in.notes
    )

    # 2. Transactionally update product stock_qty
    product.stock_qty = float(new_qty)
    if movement_in.unit_cost and float(movement_in.unit_cost) > 0:
        product.cost = float(movement_in.unit_cost)

    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement
