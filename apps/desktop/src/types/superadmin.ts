import { LicenseInfo } from './license';

export interface TenantAdminSummary {
  id: string;
  name: string;
  document?: string | null;
  is_active: boolean;
  created_at: string;
  companies_count: number;
  users_count: number;
  devices_count: number;
  license?: LicenseInfo | null;
}

export interface TenantCreateInput {
  name: string;
  document?: string;
  company_name: string;
  trade_name?: string;
  cnpj?: string;
  admin_name: string;
  admin_email: string;
  admin_password: string;
  plan_name: string;
  max_devices: number;
}

export interface TenantStatusUpdate {
  is_active: boolean;
}

export interface LicenseUpdateInput {
  plan_name?: string;
  status?: string;
  max_devices?: number;
  offline_grace_days?: number;
  expires_at?: string | null;
}

export interface SuperAdminMetrics {
  total_tenants: number;
  active_tenants: number;
  blocked_tenants: number;
  total_devices: number;
  active_devices: number;
  estimated_mrr: number;
}
