import { apiFetch } from "@/lib/apiClient";
import { useAuthStore } from "@/store/useAuthStore";
import { Product } from "@/types/product";

export const productService = {
  async getProducts(companyId?: string): Promise<Product[]> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    if (companyId) params.append("company_id", companyId);

    const rawList = await apiFetch<any[]>(`/products/?${params.toString()}`, { method: "GET" }, token);
    return rawList.map((p) => ({
      id: p.id,
      tenant_id: p.tenant_id,
      company_id: p.company_id,
      code: p.code,
      name: p.name,
      description: p.description,
      price: typeof p.price === "number" ? p.price : parseFloat(p.price || 0),
      cost_price: typeof p.cost === "number" ? p.cost : parseFloat(p.cost || p.cost_price || 0),
      stock_qty: typeof p.stock_qty === "number" ? p.stock_qty : parseFloat(p.stock_qty || 0),
      min_stock_qty: typeof p.min_stock_qty === "number" ? p.min_stock_qty : parseFloat(p.min_stock_qty || 0),
      is_active: p.is_active,
      ncm: p.ncm,
      cest: p.cest,
      category: p.category,
      unit: p.unit,
      barcodes: p.barcodes,
      barcode: p.barcodes && p.barcodes.length > 0 ? p.barcodes[0].barcode : null,
      created_at: p.created_at,
    }));
  },
};
