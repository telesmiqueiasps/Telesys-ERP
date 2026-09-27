import { apiFetch } from "@/lib/apiClient";
import { useAuthStore } from "@/store/useAuthStore";
import {
  SalesSummaryReport,
  TopProductItem,
  DREStatementReport,
  InventorySummaryReport,
} from "@/types/reports";

export const reportsService = {
  async getSalesSummary(
    companyId: string,
    startDate?: string,
    endDate?: string
  ): Promise<SalesSummaryReport> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    params.append("company_id", companyId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);

    return apiFetch<SalesSummaryReport>(`/reports/sales-summary?${params.toString()}`, { method: "GET" }, token);
  },

  async getTopProducts(companyId: string, limit: number = 20): Promise<TopProductItem[]> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    params.append("company_id", companyId);
    params.append("limit", limit.toString());

    return apiFetch<TopProductItem[]>(`/reports/top-products?${params.toString()}`, { method: "GET" }, token);
  },

  async getDREStatement(
    companyId: string,
    startDate?: string,
    endDate?: string
  ): Promise<DREStatementReport> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    params.append("company_id", companyId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);

    return apiFetch<DREStatementReport>(`/reports/dre?${params.toString()}`, { method: "GET" }, token);
  },

  async getInventoryReport(
    companyId: string,
    statusFilter?: string
  ): Promise<InventorySummaryReport> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    params.append("company_id", companyId);
    if (statusFilter) params.append("status_filter", statusFilter);

    return apiFetch<InventorySummaryReport>(`/reports/inventory?${params.toString()}`, { method: "GET" }, token);
  },
};
