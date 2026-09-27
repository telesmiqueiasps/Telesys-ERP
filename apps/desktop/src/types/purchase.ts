export interface PurchaseItemInput {
  product_id: string;
  product_name?: string;
  quantity: number;
  unit_cost: number;
}

export interface PurchaseCreateInput {
  supplier_id?: string | null;
  items: PurchaseItemInput[];
  discount_amount: number;
  notes?: string;
}

export interface PurchaseItemDetail {
  id: string;
  purchase_id: string;
  product_id: string;
  item_number: number;
  product_name: string;
  unit_code: string;
  quantity: number;
  unit_cost: number;
  total_cost: number;
}

export interface PurchaseDetail {
  id: string;
  tenant_id: string;
  company_id: string;
  supplier_id?: string | null;
  supplier_name?: string | null;
  user_id: string;
  user_name?: string | null;
  code: string;
  status: "RECEIVED" | "PENDING" | "CANCELED";
  subtotal: number;
  discount_amount: number;
  total_amount: number;
  notes?: string | null;
  items: PurchaseItemDetail[];
  created_at: string;
  updated_at: string;
}
