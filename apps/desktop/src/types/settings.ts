export interface CompanyItem {
  id: string;
  tenant_id: string;
  name: string;
  trade_name?: string | null;
  cnpj?: string | null;
  state_registration?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CompanyCreateInput {
  name: string;
  trade_name?: string;
  cnpj?: string;
  state_registration?: string;
  is_active?: boolean;
}

export interface CompanyUpdateInput extends Partial<CompanyCreateInput> {}

export interface PermissionItem {
  id: string;
  code: string;
  name: string;
  module: string;
  description?: string | null;
}

export interface RoleItem {
  id: string;
  tenant_id?: string | null;
  name: string;
  description?: string | null;
  is_system: boolean;
  permissions: PermissionItem[];
  created_at: string;
  updated_at: string;
}

export interface RoleCreateInput {
  name: string;
  description?: string;
  permission_ids: string[];
}

export interface UserItem {
  id: string;
  tenant_id: string;
  name: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  roles: RoleItem[];
  created_at: string;
  updated_at: string;
}

export interface UserCreateInput {
  name: string;
  email: string;
  password: string;
  is_active?: boolean;
  is_superuser?: boolean;
  role_ids: string[];
}

export interface UserUpdateInput {
  name?: string;
  email?: string;
  password?: string;
  is_active?: boolean;
  is_superuser?: boolean;
  role_ids?: string[];
}
