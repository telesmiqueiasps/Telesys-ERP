export type LicenseStatus = 'ACTIVE' | 'EXPIRED' | 'BLOCKED' | 'REVOKED';
export type DeviceStatus = 'AUTHORIZED' | 'REVOKED';

export interface DeviceInfo {
  id: string;
  tenant_id: string;
  license_id: string;
  device_id: string;
  device_name: string;
  os_info?: string | null;
  app_version?: string | null;
  status: DeviceStatus;
  last_heartbeat_at?: string | null;
  created_at: string;
}

export interface LicenseInfo {
  id: string;
  tenant_id: string;
  license_key: string;
  plan_name: string;
  status: LicenseStatus;
  max_devices: number;
  expires_at?: string | null;
  offline_grace_days: number;
  active_devices_count: number;
  devices: DeviceInfo[];
  created_at: string;
}

export interface LicenseActivatePayload {
  license_key: string;
  device_id: string;
  device_name: string;
  os_info?: string;
  app_version?: string;
}

export interface LicenseCache {
  license_key: string;
  plan_name: string;
  status: LicenseStatus;
  max_devices: number;
  offline_grace_days: number;
  last_sync_at: string;
  device_id: string;
}
