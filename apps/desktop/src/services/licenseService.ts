import { apiFetch } from "@/lib/apiClient";
import { useAuthStore } from "@/store/useAuthStore";
import { LicenseInfo, DeviceInfo, LicenseCache, LicenseActivatePayload } from "@/types/license";

const DEVICE_ID_KEY = "telesys_device_id";
const LICENSE_CACHE_KEY = "telesys_license_cache";

export function getOrCreateDeviceId(): string {
  let deviceId = localStorage.getItem(DEVICE_ID_KEY);
  if (!deviceId) {
    deviceId =
      "DEV-" +
      Math.random().toString(36).substring(2, 10).toUpperCase() +
      "-" +
      Date.now().toString(36).toUpperCase();
    localStorage.setItem(DEVICE_ID_KEY, deviceId);
  }
  return deviceId;
}

export function getDeviceName(): string {
  return `Terminal Desktop (${navigator.platform || "Windows"})`;
}

export const licenseService = {
  getDeviceId(): string {
    return getOrCreateDeviceId();
  },

  async getCurrentLicense(): Promise<LicenseInfo> {
    const token = useAuthStore.getState().token;
    try {
      const data = await apiFetch<LicenseInfo>("/licenses/current", { method: "GET" }, token);
      this.saveCache(data);
      return data;
    } catch (error) {
      const cache = this.getCache();
      if (cache) {
        return {
          id: "offline-id",
          tenant_id: "offline-tenant",
          license_key: cache.license_key,
          plan_name: cache.plan_name,
          status: cache.status,
          max_devices: cache.max_devices,
          offline_grace_days: cache.offline_grace_days,
          active_devices_count: 1,
          devices: [],
          created_at: cache.last_sync_at,
        };
      }
      throw error;
    }
  },

  async activateLicense(licenseKey: string): Promise<LicenseInfo> {
    const token = useAuthStore.getState().token;
    const payload: LicenseActivatePayload = {
      license_key: licenseKey,
      device_id: this.getDeviceId(),
      device_name: getDeviceName(),
      os_info: navigator.userAgent || "Windows Desktop",
      app_version: "1.0.0",
    };

    const data = await apiFetch<LicenseInfo>(
      "/licenses/activate",
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
      token
    );
    this.saveCache(data);
    return data;
  },

  async sendHeartbeat(): Promise<void> {
    const token = useAuthStore.getState().token;
    try {
      await apiFetch(
        "/licenses/heartbeat",
        {
          method: "POST",
          body: JSON.stringify({
            license_key: this.getCache()?.license_key || "UNKNOWN",
            device_id: this.getDeviceId(),
          }),
        },
        token
      );
    } catch (err) {
      console.warn("Heartbeat indisponível (modo offline).", err);
    }
  },

  async listDevices(): Promise<DeviceInfo[]> {
    const token = useAuthStore.getState().token;
    return apiFetch<DeviceInfo[]>("/licenses/devices", { method: "GET" }, token);
  },

  async revokeDevice(deviceId: string): Promise<DeviceInfo> {
    const token = useAuthStore.getState().token;
    return apiFetch<DeviceInfo>(
      `/licenses/devices/${deviceId}/revoke`,
      { method: "POST" },
      token
    );
  },

  saveCache(license: LicenseInfo): void {
    const cache: LicenseCache = {
      license_key: license.license_key,
      plan_name: license.plan_name,
      status: license.status,
      max_devices: license.max_devices,
      offline_grace_days: license.offline_grace_days,
      last_sync_at: new Date().toISOString(),
      device_id: this.getDeviceId(),
    };
    localStorage.setItem(LICENSE_CACHE_KEY, JSON.stringify(cache));
  },

  getCache(): LicenseCache | null {
    const str = localStorage.getItem(LICENSE_CACHE_KEY);
    if (!str) return null;
    try {
      return JSON.parse(str);
    } catch {
      return null;
    }
  },

  validateOfflineGrace(): { valid: boolean; daysRemaining: number; reason?: string } {
    const cache = this.getCache();
    if (!cache) {
      return { valid: false, daysRemaining: 0, reason: "Nenhuma licença em cache local." };
    }

    if (cache.status !== "ACTIVE") {
      return { valid: false, daysRemaining: 0, reason: `Status da licença: ${cache.status}` };
    }

    const lastSync = new Date(cache.last_sync_at).getTime();
    const now = new Date().getTime();
    const diffDays = Math.floor((now - lastSync) / (1000 * 60 * 60 * 24));
    const graceDays = cache.offline_grace_days || 14;

    if (diffDays > graceDays) {
      return {
        valid: false,
        daysRemaining: 0,
        reason: `Período offline ultrapassou ${graceDays} dias sem conexão ao servidor.`,
      };
    }

    return {
      valid: true,
      daysRemaining: graceDays - diffDays,
    };
  },
};
