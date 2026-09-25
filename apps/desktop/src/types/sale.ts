export interface CartItem {
  id: string; // Product UUID
  code?: string | null;
  name: string;
  unit_code: string;
  unit_price: number;
  quantity: number;
  discount_amount: number;
  total_price: number;
  ncm?: string | null;
  cest?: string | null;
}

export interface SalePaymentInput {
  payment_method: string;
  amount: number;
  change_amount: number;
}

export interface SaleCreateInput {
  customer_id?: string | null;
  items: {
    product_id: string;
    quantity: number;
    unit_price: number;
    discount_amount: number;
  }[];
  payments: SalePaymentInput[];
  discount_amount: number;
  notes?: string;
}

export interface SaleItem {
  id: string;
  sale_id: string;
  product_id: string;
  item_number: number;
  product_name: string;
  unit_code: string;
  quantity: number;
  unit_price: number;
  discount_amount: number;
  total_price: number;
  ncm?: string | null;
  cest?: string | null;
}

export interface SalePayment {
  id: string;
  sale_id: string;
  payment_method: string;
  amount: number;
  change_amount: number;
}

export interface SaleDetail {
  id: string;
  tenant_id: string;
  company_id: string;
  cash_register_id?: string | null;
  customer_id?: string | null;
  customer_name?: string | null;
  user_id: string;
  user_name?: string | null;
  code: string;
  status: "COMPLETED" | "CANCELED";
  subtotal: number;
  discount_amount: number;
  total_amount: number;
  notes?: string | null;
  items: SaleItem[];
  payments: SalePayment[];
  created_at: string;
  updated_at: string;
}
