import { apiFetch } from "@/lib/apiClient";
import { useAuthStore } from "@/store/useAuthStore";
import { UpdateCheckResponse } from "@/types/updater";

export const CURRENT_APP_VERSION = "0.1.0";

export const updaterService = {
  getAppVersion(): string {
    return CURRENT_APP_VERSION;
  },

  async checkForUpdates(): Promise<UpdateCheckResponse> {
    const token = useAuthStore.getState().token;
    const params = new URLSearchParams();
    params.append("current_version", CURRENT_APP_VERSION);

    return apiFetch<UpdateCheckResponse>(`/updates/check?${params.toString()}`, { method: "GET" }, token);
  },

  downloadUpdate(downloadUrl?: string | null): void {
    const url = downloadUrl || `https://downloads.telesys.com.br/desktop/v1.0.1/Telesys_ERP_Setup.exe`;
    window.open(url, "_blank");
  },
};
