import uuid
from typing import List, Any, Optional
from datetime import datetime, time
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, desc, extract

from app.api import deps
from app.models.user import User
from app.models.sale import Sale, SaleItem, SalePayment, SaleStatus
from app.models.product import Product
from app.models.finance import FinancialMovement
from app.schemas.reports import (
    SalesSummaryReport,
    PaymentMethodSummary,
    HourlySalesItem,
    TopProductItem,
    DREStatementReport,
    InventoryReportItem,
    InventorySummaryReport,
)


router = APIRouter()


@router.get("/sales-summary", response_model=SalesSummaryReport, summary="Resumo Consolidado de Vendas (BI)")
def get_sales_summary_report(
    company_id: uuid.UUID = Query(..., description="ID da Empresa"),
    start_date: Optional[str] = Query(None, description="Data inicial (AAAA-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Data final (AAAA-MM-DD)"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retorna indicadores resumidos de vendas, ticket médio, formas de pagamento e horários de pico.
    """
    stmt = (
        select(Sale)
        .options(selectinload(Sale.payments), selectinload(Sale.items))
        .where(
            Sale.company_id == company_id,
            Sale.tenant_id == current_user.tenant_id,
            Sale.status == SaleStatus.COMPLETED,
        )
    )

    if start_date:
        dt_start = datetime.strptime(start_date, "%Y-%m-%d")
        stmt = stmt.where(Sale.created_at >= dt_start)
    if end_date:
        dt_end = datetime.combine(datetime.strptime(end_date, "%Y-%m-%d"), time.max)
        stmt = stmt.where(Sale.created_at <= dt_end)

    sales = db.scalars(stmt).all()

    total_revenue = sum(float(s.total_amount) for s in sales)
    total_sales_count = len(sales)
    average_ticket = (total_revenue / total_sales_count) if total_sales_count > 0 else 0.0

    total_items = 0.0
    payment_map: dict[str, dict] = {}
    hourly_map: dict[int, dict] = {h: {"count": 0, "revenue": 0.0} for h in range(24)}

    for s in sales:
        hour = s.created_at.hour
        hourly_map[hour]["count"] += 1
        hourly_map[hour]["revenue"] += float(s.total_amount)

        for item in s.items:
            total_items += float(item.quantity)

        for pay in s.payments:
            pm = pay.payment_method
            amt = float(pay.amount - pay.change_amount)
            if pm not in payment_map:
                payment_map[pm] = {"total_amount": 0.0, "count": 0}
            payment_map[pm]["total_amount"] += amt
            payment_map[pm]["count"] += 1

    payment_summaries = [
        PaymentMethodSummary(
            payment_method=pm,
            total_amount=round(data["total_amount"], 2),
            count=data["count"],
        )
        for pm, data in payment_map.items()
    ]

    hourly_items = [
        HourlySalesItem(
            hour=h,
            sales_count=data["count"],
            total_revenue=round(data["revenue"], 2),
        )
        for h, data in hourly_map.items()
    ]

    return SalesSummaryReport(
        total_revenue=round(total_revenue, 2),
        total_sales_count=total_sales_count,
        average_ticket=round(average_ticket, 2),
        total_items_sold=round(total_items, 3),
        payment_methods=payment_summaries,
        hourly_distribution=hourly_items,
    )


@router.get("/top-products", response_model=List[TopProductItem], summary="Curva ABC de Produtos Mais Vendidos")
def get_top_products_report(
    company_id: uuid.UUID = Query(..., description="ID da Empresa"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retorna o ranking de produtos mais vendidos com margem de lucro calculada.
    """
    stmt = (
        select(
            SaleItem.product_id,
            SaleItem.product_name,
            func.sum(SaleItem.quantity).label("total_qty"),
            func.sum(SaleItem.total_price).label("total_revenue"),
        )
        .join(Sale, SaleItem.sale_id == Sale.id)
        .where(
            Sale.company_id == company_id,
            Sale.tenant_id == current_user.tenant_id,
            Sale.status == SaleStatus.COMPLETED,
        )
        .group_by(SaleItem.product_id, SaleItem.product_name)
        .order_by(desc("total_revenue"))
        .limit(limit)
    )

    results = db.execute(stmt).all()

    items = []
    for row in results:
        pid, name, qty, rev = row.product_id, row.product_name, float(row.total_qty or 0), float(row.total_revenue or 0)
        prod = db.get(Product, pid)
        barcode = (prod.barcodes[0].barcode if (prod and prod.barcodes) else (prod.code if prod else None))
        cost_price = float(prod.cost) if (prod and prod.cost) else 0.0

        total_cost = qty * cost_price
        profit = rev - total_cost
        profit_percent = (profit / rev * 100) if rev > 0 else 0.0

        items.append(
            TopProductItem(
                product_id=str(pid),
                product_name=name,
                barcode=barcode,
                quantity_sold=round(qty, 3),
                total_revenue=round(rev, 2),
                cost_price=round(cost_price, 2),
                profit_margin_amount=round(profit, 2),
                profit_margin_percent=round(profit_percent, 1),
            )
        )

    return items


@router.get("/dre", response_model=DREStatementReport, summary="Demonstração do Resultado do Exercício (DRE)")
def get_dre_statement_report(
    company_id: uuid.UUID = Query(..., description="ID da Empresa"),
    start_date: Optional[str] = Query(None, description="Data inicial (AAAA-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Data final (AAAA-MM-DD)"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retorna a DRE sintética do período (Receita Bruta, CMV, Lucro Bruto, Despesas Operacionais e Lucro Líquido).
    """
    # 1. Receita Bruta de Vendas
    sales_stmt = select(Sale).options(selectinload(Sale.items)).where(
        Sale.company_id == company_id,
        Sale.tenant_id == current_user.tenant_id,
        Sale.status == SaleStatus.COMPLETED,
    )

    if start_date:
        dt_start = datetime.strptime(start_date, "%Y-%m-%d")
        sales_stmt = sales_stmt.where(Sale.created_at >= dt_start)
    if end_date:
        dt_end = datetime.combine(datetime.strptime(end_date, "%Y-%m-%d"), time.max)
        sales_stmt = sales_stmt.where(Sale.created_at <= dt_end)

    sales = db.scalars(sales_stmt).all()

    gross_revenue = sum(float(s.total_amount) for s in sales)
    deductions = sum(float(s.discount_amount) for s in sales)
    net_revenue = gross_revenue - deductions

    # 2. Custo das Mercadorias Vendidas (CMV)
    cmv = 0.0
    for s in sales:
        for item in s.items:
            prod = db.get(Product, item.product_id)
            cost = float(prod.cost) if (prod and prod.cost) else 0.0
            cmv += float(item.quantity) * cost

    gross_profit = net_revenue - cmv
    gross_margin_pct = (gross_profit / net_revenue * 100) if net_revenue > 0 else 0.0

    # 3. Despesas Operacionais das movimentações financeiras de SAÍDA
    fin_stmt = select(func.sum(FinancialMovement.amount)).where(
        FinancialMovement.company_id == company_id,
        FinancialMovement.tenant_id == current_user.tenant_id,
        FinancialMovement.movement_type == "SAIDA",
    )
    if start_date:
        fin_stmt = fin_stmt.where(FinancialMovement.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        fin_stmt = fin_stmt.where(FinancialMovement.created_at <= datetime.combine(datetime.strptime(end_date, "%Y-%m-%d"), time.max))


    operating_expenses = float(db.scalar(fin_stmt) or 0.0)

    # 4. Lucro Líquido
    net_profit = gross_profit - operating_expenses
    net_margin_pct = (net_profit / net_revenue * 100) if net_revenue > 0 else 0.0

    p_start = start_date or "Início do Período"
    p_end = end_date or datetime.now().strftime("%Y-%m-%d")

    return DREStatementReport(
        period_start=p_start,
        period_end=p_end,
        gross_revenue=round(gross_revenue, 2),
        deductions=round(deductions, 2),
        net_revenue=round(net_revenue, 2),
        cost_of_goods_sold=round(cmv, 2),
        gross_profit=round(gross_profit, 2),
        gross_profit_margin_percent=round(gross_margin_pct, 1),
        operating_expenses=round(operating_expenses, 2),
        net_profit=round(net_profit, 2),
        net_profit_margin_percent=round(net_margin_pct, 1),
    )


@router.get("/inventory", response_model=InventorySummaryReport, summary="Relatório de Inventário e Valorização de Estoque")
def get_inventory_report(
    company_id: uuid.UUID = Query(..., description="ID da Empresa"),
    status_filter: Optional[str] = Query(None, description="Filtrar por status ('LOW_STOCK', 'OUT_OF_STOCK', 'NORMAL')"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retorna o inventário completo com apuração de saldo, custo total investido, valor total de venda e margem projetada.
    """
    stmt = (
        select(Product)
        .options(selectinload(Product.category), selectinload(Product.unit), selectinload(Product.barcodes))
        .where(
            Product.company_id == company_id,
            Product.tenant_id == current_user.tenant_id,
            Product.is_active == True,
        )
        .order_by(Product.name.asc())
    )

    products = db.scalars(stmt).all()

    total_units = 0.0
    total_cost_val = 0.0
    total_selling_val = 0.0
    low_stock_cnt = 0
    out_of_stock_cnt = 0

    report_items = []
    for p in products:
        stock = float(p.stock_qty or 0.0)
        min_stk = float(p.min_stock_qty or 0.0)
        cost = float(p.cost or 0.0)
        price = float(p.price or 0.0)

        cost_val = stock * cost
        sell_val = stock * price

        status_alert = "NORMAL"
        if stock <= 0:
            status_alert = "OUT_OF_STOCK"
            out_of_stock_cnt += 1
        elif stock <= min_stk:
            status_alert = "LOW_STOCK"
            low_stock_cnt += 1

        if status_filter and status_alert != status_filter:
            continue

        total_units += stock
        total_cost_val += cost_val
        total_selling_val += sell_val

        cat_name = p.category.name if p.category else "Sem Categoria"
        unit_code = p.unit.code if p.unit else "UN"
        prod_barcode = p.barcodes[0].barcode if p.barcodes else (p.code or None)

        report_items.append(
            InventoryReportItem(
                product_id=str(p.id),
                product_name=p.name,
                barcode=prod_barcode,
                category_name=cat_name,
                unit_code=unit_code,
                current_stock=round(stock, 3),
                min_stock=round(min_stk, 3),
                cost_price=round(cost, 2),
                selling_price=round(price, 2),
                total_cost_value=round(cost_val, 2),
                total_selling_value=round(sell_val, 2),
                status_alert=status_alert,
            )
        )

    potential_profit = total_selling_val - total_cost_val

    return InventorySummaryReport(
        total_products_count=len(products),
        total_units=round(total_units, 3),
        total_cost_value=round(total_cost_val, 2),
        total_selling_value=round(total_selling_val, 2),
        total_potential_profit=round(potential_profit, 2),
        low_stock_count=low_stock_cnt,
        out_of_stock_count=out_of_stock_cnt,
        items=report_items,
    )

