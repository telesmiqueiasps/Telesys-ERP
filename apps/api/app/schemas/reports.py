from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class PaymentMethodSummary(BaseModel):
    payment_method: str
    total_amount: float
    count: int


class TopProductItem(BaseModel):
    product_id: str
    product_name: str
    barcode: Optional[str] = None
    quantity_sold: float
    total_revenue: float
    cost_price: float
    profit_margin_amount: float
    profit_margin_percent: float


class HourlySalesItem(BaseModel):
    hour: int
    sales_count: int
    total_revenue: float


class SalesSummaryReport(BaseModel):
    total_revenue: float
    total_sales_count: int
    average_ticket: float
    total_items_sold: float
    payment_methods: List[PaymentMethodSummary]
    hourly_distribution: List[HourlySalesItem]


class DREStatementReport(BaseModel):
    period_start: str
    period_end: str
    gross_revenue: float
    deductions: float
    net_revenue: float
    cost_of_goods_sold: float
    gross_profit: float
    gross_profit_margin_percent: float
    operating_expenses: float
    net_profit: float
    net_profit_margin_percent: float


class InventoryReportItem(BaseModel):
    product_id: str
    product_name: str
    barcode: Optional[str] = None
    category_name: Optional[str] = None
    unit_code: str = "UN"
    current_stock: float
    min_stock: float
    cost_price: float
    selling_price: float
    total_cost_value: float
    total_selling_value: float
    status_alert: str  # 'NORMAL', 'LOW_STOCK', 'OUT_OF_STOCK'


class InventorySummaryReport(BaseModel):
    total_products_count: int
    total_units: float
    total_cost_value: float
    total_selling_value: float
    total_potential_profit: float
    low_stock_count: int
    out_of_stock_count: int
    items: List[InventoryReportItem]
