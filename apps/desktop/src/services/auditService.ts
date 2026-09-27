import { apiFetch } from "@/lib/apiClient";
import { useAuthStore } from "@/store/useAuthStore";
import { AuditLogItem, AuditFilterParams } from "@/types/audit";

export const auditService = {
  async getAuditLogs(companyId?: string, params?: AuditFilterParams): Promise<AuditLogItem[]> {
    const token = useAuthStore.getState().token;
    const urlParams = new URLSearchParams();
    if (companyId) urlParams.append("company_id", companyId);
    if (params?.entity) urlParams.append("entity", params.entity);
    if (params?.action) urlParams.append("action", params.action);
    if (params?.user_id) urlParams.append("user_id", params.user_id);
    if (params?.limit) urlParams.append("limit", params.limit.toString());

    return apiFetch<AuditLogItem[]>(`/audit/logs?${urlParams.toString()}`, { method: "GET" }, token);
  },

  async getAuditDetail(id: string): Promise<AuditLogItem> {
    const token = useAuthStore.getState().token;
    return apiFetch<AuditLogItem>(`/audit/logs/${id}`, { method: "GET" }, token);
  },
};
