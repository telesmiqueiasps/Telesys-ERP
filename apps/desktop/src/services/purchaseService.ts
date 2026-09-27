import { apiFetch } from "@/lib/apiClient";
import { useAuthStore } from "@/store/useAuthStore";
import { PurchaseCreateInput, PurchaseDetail } from "@/types/purchase";
import { NfeParseResponse, NfeConfirmImportInput } from "@/types/xmlImport";

export const purchaseService = {
  async getPurchases(companyId?: string): Promise<PurchaseDetail[]> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    if (companyId) params.append("company_id", companyId);

    return apiFetch<PurchaseDetail[]>(`/purchases/?${params.toString()}`, { method: "GET" }, token);
  },

  async getPurchaseDetail(id: string): Promise<PurchaseDetail> {
    const token = useAuthStore.getState().token;
    return apiFetch<PurchaseDetail>(`/purchases/${id}`, { method: "GET" }, token);
  },

  async createPurchase(data: PurchaseCreateInput, companyId?: string): Promise<PurchaseDetail> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    if (companyId) params.append("company_id", companyId);

    return apiFetch<PurchaseDetail>(
      `/purchases/?${params.toString()}`,
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      token
    );
  },

  async cancelPurchase(id: string): Promise<PurchaseDetail> {
    const token = useAuthStore.getState().token;
    return apiFetch<PurchaseDetail>(`/purchases/${id}/cancel`, { method: "POST" }, token);
  },

  async parseNfeXml(file: File, companyId?: string): Promise<NfeParseResponse> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    if (companyId) params.append("company_id", companyId);

    const formData = new FormData();
    formData.append("file", file);

    const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api/v1";
    const response = await fetch(`${API_BASE_URL}/purchases/parse-xml?${params.toString()}`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || "Falha ao processar arquivo XML de NF-e.");
    }

    return response.json();
  },

  async confirmNfeXml(data: NfeConfirmImportInput, companyId?: string): Promise<PurchaseDetail> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    if (companyId) params.append("company_id", companyId);

    return apiFetch<PurchaseDetail>(
      `/purchases/confirm-xml?${params.toString()}`,
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      token
    );
  },
};
