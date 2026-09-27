import { apiFetch } from "@/lib/apiClient";
import { useAuthStore } from "@/store/useAuthStore";
import { BackupRecord, BackupCreateResult } from "@/types/backup";

const LOCAL_BACKUP_KEY = "telesys_backup_history";

export const backupService = {
  getLocalBackups(): BackupRecord[] {
    const raw = localStorage.getItem(LOCAL_BACKUP_KEY);
    if (!raw) return [];
    try {
      return JSON.parse(raw);
    } catch {
      return [];
    }
  },

  saveLocalBackupRecord(record: BackupRecord): void {
    const history = this.getLocalBackups();
    history.unshift(record);
    localStorage.setItem(LOCAL_BACKUP_KEY, JSON.stringify(history.slice(0, 30))); // guarda até 30 backups locais
  },

  async createBackup(sendToCloud: boolean = true): Promise<BackupCreateResult> {
    const token = useAuthStore.getState().token;
    const now = new Date();
    const timestampStr = now.toISOString().replace(/[:.]/g, "-");
    const filename = `telesys_backup_${timestampStr}.json`;

    // 1. Empacotar estado local completo
    const backupPayload = {
      version: "1.0.0",
      created_at: now.toISOString(),
      master_companies: localStorage.getItem("telesys_master_companies"),
      license_cache: localStorage.getItem("telesys_license_cache"),
      device_id: localStorage.getItem("telesys_device_id"),
      offline_sync_queue: localStorage.getItem("telesys_offline_sync_queue"),
    };

    const jsonString = JSON.stringify(backupPayload, null, 2);
    const sizeBytes = new Blob([jsonString]).size;

    const localRecord: BackupRecord = {
      id: "LOCAL-" + Date.now().toString(36),
      filename,
      size_bytes: sizeBytes,
      type: "LOCAL",
      created_at: now.toISOString(),
      hash: "SHA256-" + Math.random().toString(36).substring(2, 12).toUpperCase(),
    };

    // Salvar no histórico local e salvar payload localmente no localStorage
    this.saveLocalBackupRecord(localRecord);
    localStorage.setItem(`telesys_backup_data_${localRecord.id}`, jsonString);

    let cloudSynced = false;
    let cloudError: string | undefined = undefined;

    // 2. Enviar para a nuvem se solicitado e se online
    if (sendToCloud && token) {
      try {
        const formData = new FormData();
        const fileBlob = new Blob([jsonString], { type: "application/json" });
        formData.append("file", fileBlob, filename);

        const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api/v1";
        const response = await fetch(`${API_BASE_URL}/backups/upload`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        });

        if (response.ok) {
          cloudSynced = true;
        } else {
          const errData = await response.json();
          cloudError = errData?.detail || "Erro ao enviar para a nuvem.";
        }
      } catch (err: any) {
        cloudError = "Servidor indisponível no momento (modo offline).";
      }
    }

    return {
      record: localRecord,
      cloudSynced,
      error: cloudError,
    };
  },

  async listCloudBackups(): Promise<BackupRecord[]> {
    const token = useAuthStore.getState().token;
    if (!token) return [];
    try {
      return await apiFetch<BackupRecord[]>("/backups/cloud", { method: "GET" }, token);
    } catch {
      return [];
    }
  },

  async downloadCloudBackup(filename: string): Promise<void> {
    const token = useAuthStore.getState().token;
    if (!token) return;

    const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api/v1";
    const res = await fetch(`${API_BASE_URL}/backups/cloud/${filename}/download`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!res.ok) throw new Error("Erro ao baixar backup da nuvem.");

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
  },

  restoreBackup(backupId: string): boolean {
    const rawData = localStorage.getItem(`telesys_backup_data_${backupId}`);
    if (!rawData) return false;

    try {
      const data = JSON.parse(rawData);
      if (data.master_companies) localStorage.setItem("telesys_master_companies", data.master_companies);
      if (data.license_cache) localStorage.setItem("telesys_license_cache", data.license_cache);
      if (data.device_id) localStorage.setItem("telesys_device_id", data.device_id);
      if (data.offline_sync_queue) localStorage.setItem("telesys_offline_sync_queue", data.offline_sync_queue);
      return true;
    } catch (err) {
      console.error("Erro ao restaurar backup:", err);
      return false;
    }
  },

  deleteLocalBackup(backupId: string): void {
    const history = this.getLocalBackups().filter((b) => b.id !== backupId);
    localStorage.setItem(LOCAL_BACKUP_KEY, JSON.stringify(history));
    localStorage.removeItem(`telesys_backup_data_${backupId}`);
  },
};
