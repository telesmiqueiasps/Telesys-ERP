export interface AuditLogItem {
  id: string;
  tenant_id: string;
  company_id: string;
  user_id: string;
  user_name?: string | null;
  action: string;
  entity: string;
  entity_id?: string | null;
  before_data?: string | null;
  after_data?: string | null;
  device_id?: string | null;
  ip_address?: string | null;
  created_at: string;
}

export interface AuditFilterParams {
  entity?: string;
  action?: string;
  user_id?: string;
  limit?: number;
}
