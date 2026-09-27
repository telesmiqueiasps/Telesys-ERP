import { apiFetch } from "@/lib/apiClient";
import { useAuthStore } from "@/store/useAuthStore";
import {
  TenantAdminSummary,
  TenantCreateInput,
  TenantStatusUpdate,
  LicenseUpdateInput,
  SuperAdminMetrics,
} from "@/types/superadmin";
import { LicenseInfo } from "@/types/license";

export const superadminService = {
  async getMetrics(): Promise<SuperAdminMetrics> {
    const token = useAuthStore.getState().token;
    return apiFetch<SuperAdminMetrics>("/superadmin/metrics", { method: "GET" }, token);
  },

  async getTenants(): Promise<TenantAdminSummary[]> {
    const token = useAuthStore.getState().token;
    return apiFetch<TenantAdminSummary[]>("/superadmin/tenants", { method: "GET" }, token);
  },

  async createTenant(input: TenantCreateInput): Promise<TenantAdminSummary> {
    const token = useAuthStore.getState().token;
    return apiFetch<TenantAdminSummary>(
      "/superadmin/tenants",
      {
        method: "POST",
        body: JSON.stringify(input),
      },
      token
    );
  },

  async updateTenantStatus(tenantId: string, isActive: boolean): Promise<TenantAdminSummary> {
    const token = useAuthStore.getState().token;
    const body: TenantStatusUpdate = { is_active: isActive };
    return apiFetch<TenantAdminSummary>(
      `/superadmin/tenants/${tenantId}/status`,
      {
        method: "PUT",
        body: JSON.stringify(body),
      },
      token
    );
  },

  async updateLicense(licenseId: string, input: LicenseUpdateInput): Promise<LicenseInfo> {
    const token = useAuthStore.getState().token;
    return apiFetch<LicenseInfo>(
      `/superadmin/licenses/${licenseId}`,
      {
        method: "PUT",
        body: JSON.stringify(input),
      },
      token
    );
  },
};
