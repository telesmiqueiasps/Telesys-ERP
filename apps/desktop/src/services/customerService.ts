import { apiFetch } from "@/lib/apiClient";
import { useAuthStore } from "@/store/useAuthStore";
import {
  Customer,
  CustomerCreateInput,
  CustomerUpdateInput,
  Supplier,
  SupplierCreateInput,
  SupplierUpdateInput,
} from "@/types/customer";

export const customerService = {
  // Customers API
  async getCustomers(companyId?: string, search?: string, isActive?: boolean): Promise<Customer[]> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    if (companyId) params.append("company_id", companyId);
    if (search) params.append("search", search);
    if (isActive !== undefined) params.append("is_active", String(isActive));

    return apiFetch<Customer[]>(`/customers/?${params.toString()}`, { method: "GET" }, token);
  },

  async createCustomer(data: CustomerCreateInput): Promise<Customer> {
    const token = useAuthStore.getState().token;
    return apiFetch<Customer>(
      "/customers/",
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      token
    );
  },

  async updateCustomer(id: string, data: CustomerUpdateInput): Promise<Customer> {
    const token = useAuthStore.getState().token;
    return apiFetch<Customer>(
      `/customers/${id}`,
      {
        method: "PUT",
        body: JSON.stringify(data),
      },
      token
    );
  },

  async deleteCustomer(id: string): Promise<Customer> {
    const token = useAuthStore.getState().token;
    return apiFetch<Customer>(`/customers/${id}`, { method: "DELETE" }, token);
  },

  // Suppliers API
  async getSuppliers(companyId?: string, search?: string, isActive?: boolean): Promise<Supplier[]> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    if (companyId) params.append("company_id", companyId);
    if (search) params.append("search", search);
    if (isActive !== undefined) params.append("is_active", String(isActive));

    return apiFetch<Supplier[]>(`/suppliers/?${params.toString()}`, { method: "GET" }, token);
  },

  async createSupplier(data: SupplierCreateInput): Promise<Supplier> {
    const token = useAuthStore.getState().token;
    return apiFetch<Supplier>(
      "/suppliers/",
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      token
    );
  },

  async updateSupplier(id: string, data: SupplierUpdateInput): Promise<Supplier> {
    const token = useAuthStore.getState().token;
    return apiFetch<Supplier>(
      `/suppliers/${id}`,
      {
        method: "PUT",
        body: JSON.stringify(data),
      },
      token
    );
  },

  async deleteSupplier(id: string): Promise<Supplier> {
    const token = useAuthStore.getState().token;
    return apiFetch<Supplier>(`/suppliers/${id}`, { method: "DELETE" }, token);
  },
};
