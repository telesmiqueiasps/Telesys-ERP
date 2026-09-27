import { apiFetch } from "@/lib/apiClient";
import { useAuthStore } from "@/store/useAuthStore";
import {
  CompanyItem,
  CompanyCreateInput,
  CompanyUpdateInput,
  UserItem,
  UserCreateInput,
  UserUpdateInput,
  RoleItem,
  RoleCreateInput,
  PermissionItem,
} from "@/types/settings";

export const settingsService = {
  // Companies / Filiais API
  async getCompanies(): Promise<CompanyItem[]> {
    const token = useAuthStore.getState().token;
    return apiFetch<CompanyItem[]>("/companies", { method: "GET" }, token);
  },

  async createCompany(data: CompanyCreateInput): Promise<CompanyItem> {
    const token = useAuthStore.getState().token;
    const tenantId = useAuthStore.getState().user?.tenant_id;
    return apiFetch<CompanyItem>(
      "/companies",
      {
        method: "POST",
        body: JSON.stringify({ ...data, tenant_id: tenantId }),
      },
      token
    );
  },

  async updateCompany(id: string, data: CompanyUpdateInput): Promise<CompanyItem> {
    const token = useAuthStore.getState().token;
    return apiFetch<CompanyItem>(
      `/companies/${id}`,
      {
        method: "PUT",
        body: JSON.stringify(data),
      },
      token
    );
  },

  // Users API
  async getUsers(): Promise<UserItem[]> {
    const token = useAuthStore.getState().token;
    return apiFetch<UserItem[]>("/users", { method: "GET" }, token);
  },

  async createUser(data: UserCreateInput): Promise<UserItem> {
    const token = useAuthStore.getState().token;
    const tenantId = useAuthStore.getState().user?.tenant_id;
    return apiFetch<UserItem>(
      "/users",
      {
        method: "POST",
        body: JSON.stringify({ ...data, tenant_id: tenantId }),
      },
      token
    );
  },

  async updateUser(id: string, data: UserUpdateInput): Promise<UserItem> {
    const token = useAuthStore.getState().token;
    return apiFetch<UserItem>(
      `/users/${id}`,
      {
        method: "PUT",
        body: JSON.stringify(data),
      },
      token
    );
  },

  // Roles & Permissions API
  async getRoles(): Promise<RoleItem[]> {
    const token = useAuthStore.getState().token;
    return apiFetch<RoleItem[]>("/roles", { method: "GET" }, token);
  },

  async createRole(data: RoleCreateInput): Promise<RoleItem> {
    const token = useAuthStore.getState().token;
    const tenantId = useAuthStore.getState().user?.tenant_id;
    return apiFetch<RoleItem>(
      "/roles",
      {
        method: "POST",
        body: JSON.stringify({ ...data, tenant_id: tenantId }),
      },
      token
    );
  },

  async getPermissions(): Promise<PermissionItem[]> {
    const token = useAuthStore.getState().token;
    return apiFetch<PermissionItem[]>("/roles/permissions", { method: "GET" }, token);
  },
};
