export interface FinancialCategory {
  id: string;
  tenant_id: string;
  company_id: string;
  name: string;
  type: "RECEITA" | "DESPESA";
  color?: string | null;
  is_active: boolean;
}

export interface AccountPayable {
  id: string;
  tenant_id: string;
  company_id: string;
  supplier_id?: string | null;
  supplier_name?: string | null;
  category_id?: string | null;
  category_name?: string | null;
  purchase_id?: string | null;
  description: string;
  amount: number;
  paid_amount: number;
  due_date: string;
  paid_at?: string | null;
  status: "PENDING" | "PAID" | "OVERDUE" | "CANCELED";
  payment_method?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface AccountReceivable {
  id: string;
  tenant_id: string;
  company_id: string;
  customer_id?: string | null;
  customer_name?: string | null;
  category_id?: string | null;
  category_name?: string | null;
  sale_id?: string | null;
  description: string;
  amount: number;
  received_amount: number;
  due_date: string;
  received_at?: string | null;
  status: "PENDING" | "RECEIVED" | "OVERDUE" | "CANCELED";
  payment_method?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface FinancialSummary {
  total_receivable_pending: number;
  total_payable_pending: number;
  total_overdue: number;
  forecast_balance: number;
}
