export interface PaymentMethodSummary {
  payment_method: string;
  total_amount: number;
  count: number;
}

export interface HourlySalesItem {
  hour: number;
  sales_count: number;
  total_revenue: number;
}

export interface SalesSummaryReport {
  total_revenue: number;
  total_sales_count: number;
  average_ticket: number;
  total_items_sold: number;
  payment_methods: PaymentMethodSummary[];
  hourly_distribution: HourlySalesItem[];
}

export interface TopProductItem {
  product_id: string;
  product_name: string;
  barcode?: string | null;
  quantity_sold: number;
  total_revenue: number;
  cost_price: number;
  profit_margin_amount: number;
  profit_margin_percent: number;
}

export interface DREStatementReport {
  period_start: string;
  period_end: string;
  gross_revenue: number;
  deductions: number;
  net_revenue: number;
  cost_of_goods_sold: number;
  gross_profit: number;
  gross_profit_margin_percent: number;
  operating_expenses: number;
  net_profit: number;
  net_profit_margin_percent: number;
}

export interface InventoryReportItem {
  product_id: string;
  product_name: string;
  barcode?: string | null;
  category_name?: string | null;
  unit_code: string;
  current_stock: number;
  min_stock: number;
  cost_price: number;
  selling_price: number;
  total_cost_value: number;
  total_selling_value: number;
  status_alert: 'NORMAL' | 'LOW_STOCK' | 'OUT_OF_STOCK';
}

export interface InventorySummaryReport {
  total_products_count: number;
  total_units: number;
  total_cost_value: number;
  total_selling_value: number;
  total_potential_profit: number;
  low_stock_count: number;
  out_of_stock_count: number;
  items: InventoryReportItem[];
}
