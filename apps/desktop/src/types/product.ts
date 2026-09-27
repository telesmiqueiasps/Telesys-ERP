export interface Product {
  id: string;
  tenant_id: string;
  company_id: string;
  code?: string | null;
  name: string;
  description?: string | null;
  price: number;
  cost_price: number;
  stock_qty: number;
  min_stock_qty: number;
  is_active: boolean;
  ncm?: string | null;
  cest?: string | null;
  category?: { id: string; name: string } | null;
  unit?: { id: string; code: string; name: string } | null;
  barcodes?: Array<{ id: string; barcode: string }>;
  barcode?: string | null;
  created_at?: string;
}
