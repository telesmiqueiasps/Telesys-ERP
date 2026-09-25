import { apiFetch } from "@/lib/apiClient";
import { useAuthStore } from "@/store/useAuthStore";
import {
  CashRegisterDetail,
  CashRegisterOpenInput,
  CashRegisterCloseInput,
  CashMovementCreateInput,
  CashMovement,
} from "@/types/cash";

export const cashService = {
  async getCurrentCash(companyId?: string): Promise<CashRegisterDetail | null> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    if (companyId) params.append("company_id", companyId);

    return apiFetch<CashRegisterDetail | null>(`/cash/current?${params.toString()}`, { method: "GET" }, token);
  },

  async openCash(data: CashRegisterOpenInput, companyId?: string): Promise<CashRegisterDetail> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    if (companyId) params.append("company_id", companyId);

    return apiFetch<CashRegisterDetail>(
      `/cash/open?${params.toString()}`,
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      token
    );
  },

  async createMovement(data: CashMovementCreateInput, companyId?: string): Promise<CashMovement> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    if (companyId) params.append("company_id", companyId);

    return apiFetch<CashMovement>(
      `/cash/movements?${params.toString()}`,
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      token
    );
  },

  async closeCash(data: CashRegisterCloseInput, companyId?: string): Promise<CashRegisterDetail> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    if (companyId) params.append("company_id", companyId);

    return apiFetch<CashRegisterDetail>(
      `/cash/close?${params.toString()}`,
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      token
    );
  },

  async getCashHistory(companyId?: string): Promise<CashRegisterDetail[]> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    if (companyId) params.append("company_id", companyId);

    return apiFetch<CashRegisterDetail[]>(`/cash/history?${params.toString()}`, { method: "GET" }, token);
  },
};
