import { apiFetch } from "@/lib/apiClient";
import { useAuthStore } from "@/store/useAuthStore";
import {
  FinancialCategory,
  AccountPayable,
  AccountReceivable,
  FinancialSummary,
} from "@/types/finance";

export const financeService = {
  // Categorias
  async getCategories(companyId?: string): Promise<FinancialCategory[]> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    if (companyId) params.append("company_id", companyId);

    return apiFetch<FinancialCategory[]>(`/finance/categories?${params.toString()}`, { method: "GET" }, token);
  },

  async createCategory(
    data: { name: string; type: "RECEITA" | "DESPESA"; color?: string },
    companyId?: string
  ): Promise<FinancialCategory> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    if (companyId) params.append("company_id", companyId);

    return apiFetch<FinancialCategory>(
      `/finance/categories?${params.toString()}`,
      { method: "POST", body: JSON.stringify(data) },
      token
    );
  },

  // Contas a Pagar
  async getPayables(companyId?: string): Promise<AccountPayable[]> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    if (companyId) params.append("company_id", companyId);

    return apiFetch<AccountPayable[]>(`/finance/payables?${params.toString()}`, { method: "GET" }, token);
  },

  async createPayable(
    data: {
      description: string;
      amount: number;
      due_date: string;
      supplier_id?: string | null;
      category_id?: string | null;
      notes?: string;
    },
    companyId?: string
  ): Promise<AccountPayable> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    if (companyId) params.append("company_id", companyId);

    return apiFetch<AccountPayable>(
      `/finance/payables?${params.toString()}`,
      { method: "POST", body: JSON.stringify(data) },
      token
    );
  },

  async payAccountPayable(
    id: string,
    paidAmount: number,
    paymentMethod: string
  ): Promise<AccountPayable> {
    const token = useAuthStore.getState().token;
    return apiFetch<AccountPayable>(
      `/finance/payables/${id}/pay`,
      {
        method: "POST",
        body: JSON.stringify({ paid_amount: paidAmount, payment_method: paymentMethod }),
      },
      token
    );
  },

  // Contas a Receber
  async getReceivables(companyId?: string): Promise<AccountReceivable[]> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    if (companyId) params.append("company_id", companyId);

    return apiFetch<AccountReceivable[]>(`/finance/receivables?${params.toString()}`, { method: "GET" }, token);
  },

  async createReceivable(
    data: {
      description: string;
      amount: number;
      due_date: string;
      customer_id?: string | null;
      category_id?: string | null;
      notes?: string;
    },
    companyId?: string
  ): Promise<AccountReceivable> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    if (companyId) params.append("company_id", companyId);

    return apiFetch<AccountReceivable>(
      `/finance/receivables?${params.toString()}`,
      { method: "POST", body: JSON.stringify(data) },
      token
    );
  },

  async receiveAccountReceivable(
    id: string,
    receivedAmount: number,
    paymentMethod: string
  ): Promise<AccountReceivable> {
    const token = useAuthStore.getState().token;
    return apiFetch<AccountReceivable>(
      `/finance/receivables/${id}/receive`,
      {
        method: "POST",
        body: JSON.stringify({ received_amount: receivedAmount, payment_method: paymentMethod }),
      },
      token
    );
  },

  // Indicadores
  async getFinancialSummary(companyId?: string): Promise<FinancialSummary> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    if (companyId) params.append("company_id", companyId);

    return apiFetch<FinancialSummary>(`/finance/summary?${params.toString()}`, { method: "GET" }, token);
  },
};
