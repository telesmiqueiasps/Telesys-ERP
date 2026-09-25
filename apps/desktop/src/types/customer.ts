export interface Customer {
  id: string;
  tenant_id: string;
  company_id: string;
  name: string;
  trade_name?: string | null;
  document?: string | null;
  phone?: string | null;
  email?: string | null;
  address_street?: string | null;
  address_number?: string | null;
  address_neighborhood?: string | null;
  city?: string | null;
  state?: string | null;
  postal_code?: string | null;
  notes?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CustomerCreateInput {
  name: string;
  trade_name?: string;
  document?: string;
  phone?: string;
  email?: string;
  address_street?: string;
  address_number?: string;
  address_neighborhood?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  notes?: string;
  is_active?: boolean;
}

export interface CustomerUpdateInput extends Partial<CustomerCreateInput> {}

export interface Supplier {
  id: string;
  tenant_id: string;
  company_id: string;
  name: string;
  trade_name?: string | null;
  document?: string | null;
  state_registration?: string | null;
  phone?: string | null;
  email?: string | null;
  contact_person?: string | null;
  address_street?: string | null;
  address_number?: string | null;
  address_neighborhood?: string | null;
  city?: string | null;
  state?: string | null;
  postal_code?: string | null;
  notes?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SupplierCreateInput {
  name: string;
  trade_name?: string;
  document?: string;
  state_registration?: string;
  phone?: string;
  email?: string;
  contact_person?: string;
  address_street?: string;
  address_number?: string;
  address_neighborhood?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  notes?: string;
  is_active?: boolean;
}

export interface SupplierUpdateInput extends Partial<SupplierCreateInput> {}
