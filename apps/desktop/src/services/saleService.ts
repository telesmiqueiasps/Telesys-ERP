import { apiFetch } from "@/lib/apiClient";
import { useAuthStore } from "@/store/useAuthStore";
import { SaleCreateInput, SaleDetail } from "@/types/sale";

export const saleService = {
  async createSale(data: SaleCreateInput, companyId?: string): Promise<SaleDetail> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    if (companyId) params.append("company_id", companyId);

    return apiFetch<SaleDetail>(
      `/sales/?${params.toString()}`,
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      token
    );
  },

  async getSales(companyId?: string): Promise<SaleDetail[]> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    if (companyId) params.append("company_id", companyId);

    return apiFetch<SaleDetail[]>(`/sales/?${params.toString()}`, { method: "GET" }, token);
  },

  async getSaleDetail(id: string): Promise<SaleDetail> {
    const token = useAuthStore.getState().token;
    return apiFetch<SaleDetail>(`/sales/${id}`, { method: "GET" }, token);
  },
};
