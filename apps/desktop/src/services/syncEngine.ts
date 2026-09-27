import { apiFetch } from "@/lib/apiClient";
import { useAuthStore } from "@/store/useAuthStore";
import { backupService } from "@/services/backupService";
import {
  SyncQueueItem,
  SyncStatusStats,
  EntityType,
  SyncAction,
} from "@/types/sync";


const STORAGE_KEY = "telesys_sync_queue";
const LAST_SYNC_KEY = "telesys_last_sync_at";

class SyncEngine {
  private queue: SyncQueueItem[] = [];
  private listeners: Set<(stats: SyncStatusStats) => void> = new Set();
  private isOnline: boolean = typeof navigator !== "undefined" ? navigator.onLine : true;
  private isSyncing: boolean = false;
  private workerInterval: number | null = null;

  constructor() {
    this.loadQueueFromStorage();
    if (typeof window !== "undefined") {
      window.addEventListener("online", () => this.handleConnectivityChange(true));
      window.addEventListener("offline", () => this.handleConnectivityChange(false));
    }
  }

  private loadQueueFromStorage() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        this.queue = JSON.parse(stored);
      }
    } catch (error) {
      console.error("[SyncEngine] Erro ao carregar fila do localStorage:", error);
      this.queue = [];
    }
  }

  private saveQueueToStorage() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.queue));
      this.notifyListeners();
    } catch (error) {
      console.error("[SyncEngine] Erro ao salvar fila no localStorage:", error);
    }
  }

  private handleConnectivityChange(online: boolean) {
    this.isOnline = online;
    this.notifyListeners();
    if (online) {
      this.pushPendingBatch();
    }
  }

  /**
   * Verifica a conectividade real com a API backend Cloud.
   */
  public async checkApiHealth(): Promise<boolean> {
    try {
      const token = useAuthStore.getState().token;
      if (!token) {
        this.isOnline = navigator.onLine;
        this.notifyListeners();
        return this.isOnline;
      }
      const res = await apiFetch<{ status: string }>("/sync/status", { method: "GET" }, token);
      this.isOnline = res.status === "ONLINE";
    } catch (err) {
      this.isOnline = false;
    }
    this.notifyListeners();
    return this.isOnline;
  }

  /**
   * Adiciona um evento à fila de sincronização offline-first.
   */
  public enqueueEvent(params: {
    tenant_id: string;
    company_id: string;
    entity_type: EntityType;
    action: SyncAction;
    payload: Record<string, any>;
  }): SyncQueueItem {
    const eventId = `evt_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    const newItem: SyncQueueItem = {
      id: eventId,
      event_id: eventId,
      tenant_id: params.tenant_id,
      company_id: params.company_id,
      entity_type: params.entity_type,
      action: params.action,
      payload: params.payload,
      status: "PENDING",
      attempts: 0,
      created_at: new Date().toISOString(),
    };

    this.queue.push(newItem);
    this.saveQueueToStorage();

    // Se estiver online, tentar sincronizar imediatamente
    if (this.isOnline) {
      setTimeout(() => this.pushPendingBatch(), 100);
    }

    return newItem;
  }

  /**
   * Processa e envia os eventos pendentes para a rota POST /api/v1/sync/push
   */
  public async pushPendingBatch(): Promise<{ successCount: number; failureCount: number }> {
    if (this.isSyncing) return { successCount: 0, failureCount: 0 };

    const pendingItems = this.queue.filter((item) => item.status === "PENDING" || item.status === "FAILED");
    if (pendingItems.length === 0) return { successCount: 0, failureCount: 0 };

    const token = useAuthStore.getState().token;
    if (!token) {
      return { successCount: 0, failureCount: 0 };
    }

    this.isSyncing = true;
    // Marcar como SYNCING
    pendingItems.forEach((item) => {
      item.status = "SYNCING";
      item.attempts += 1;
    });
    this.saveQueueToStorage();

    let successCount = 0;
    let failureCount = 0;

    try {
      const payloadEvents = pendingItems.map((item) => ({
        event_id: item.event_id,
        tenant_id: item.tenant_id,
        company_id: item.company_id,
        entity_type: item.entity_type,
        action: item.action,
        payload: item.payload,
        created_at: item.created_at,
      }));

      const response = await apiFetch<{
        results: Array<{ event_id: string; status: "SYNCED" | "FAILED"; message?: string }>;
      }>(
        "/sync/push",
        {
          method: "POST",
          body: JSON.stringify({ events: payloadEvents }),
        },
        token
      );

      const resultMap = new Map(response.results.map((r) => [r.event_id, r]));

      for (const item of pendingItems) {
        const res = resultMap.get(item.event_id);
        if (res && res.status === "SYNCED") {
          item.status = "SYNCED";
          item.synced_at = new Date().toISOString();
          item.last_error = null;
          successCount++;
        } else {
          item.status = "FAILED";
          item.last_error = res?.message || "Erro desconhecido ao processar lote no Cloud.";
          failureCount++;
        }
      }

      localStorage.setItem(LAST_SYNC_KEY, new Date().toISOString());
      this.isOnline = true;
    } catch (error: any) {
      console.error("[SyncEngine] Falha ao enviar lote de eventos:", error);
      this.isOnline = false;
      for (const item of pendingItems) {
        item.status = "FAILED";
        item.last_error = error.message || "Falha na conexão de rede.";
        failureCount++;
      }
    } finally {
      this.isSyncing = false;
      this.saveQueueToStorage();
    }

    return { successCount, failureCount };
  }

  /**
   * Retorna os itens atuais da fila
   */
  public getQueue(): SyncQueueItem[] {
    return [...this.queue];
  }

  /**
   * Retorna as estatísticas resumidas da engine de sincronização
   */
  public getStats(): SyncStatusStats {
    const pendingCount = this.queue.filter((i) => i.status === "PENDING").length;
    const syncingCount = this.queue.filter((i) => i.status === "SYNCING").length;
    const syncedCount = this.queue.filter((i) => i.status === "SYNCED").length;
    const failedCount = this.queue.filter((i) => i.status === "FAILED").length;
    const lastSyncAt = localStorage.getItem(LAST_SYNC_KEY);

    return {
      isOnline: this.isOnline,
      pendingCount,
      syncingCount,
      syncedCount,
      failedCount,
      lastSyncAt,
    };
  }

  /**
   * Limpa itens que já foram sincronizados com sucesso
   */
  public clearSynced(): void {
    this.queue = this.queue.filter((item) => item.status !== "SYNCED");
    this.saveQueueToStorage();
  }

  /**
   * Registra um listener para atualizações de estado do SyncEngine
   */
  public subscribe(listener: (stats: SyncStatusStats) => void): () => void {
    this.listeners.add(listener);
    listener(this.getStats());
    return () => {
      this.listeners.delete(listener);
    };
  }

  private notifyListeners() {
    const stats = this.getStats();
    this.listeners.forEach((listener) => listener(stats));
  }

  private checkAndTriggerAutoBackup() {
    try {
      const today = new Date().toISOString().split("T")[0];
      const lastBackupDate = localStorage.getItem("telesys_last_auto_backup_date");

      if (lastBackupDate !== today) {
        localStorage.setItem("telesys_last_auto_backup_date", today);
        backupService
          .createBackup(true)
          .then((res) => console.log("[SyncEngine] Backup automático diário executado:", res.record.filename))
          .catch((err) => console.warn("[SyncEngine] Erro no backup automático diário:", err));
      }
    } catch {
      // Ignorar erros em background
    }
  }

  /**
   * Inicia o worker em segundo plano que executa a cada `intervalMs` ms
   */
  public startWorker(intervalMs: number = 12000): () => void {
    if (this.workerInterval) clearInterval(this.workerInterval);

    // Executa verificação inicial e disparo de backup diário
    this.checkApiHealth().then((online) => {
      if (online) {
        this.pushPendingBatch();
        this.checkAndTriggerAutoBackup();
      }
    });

    this.workerInterval = window.setInterval(() => {
      this.checkApiHealth().then((online) => {
        if (online) {
          this.pushPendingBatch();
          this.checkAndTriggerAutoBackup();
        }
      });
    }, intervalMs);

    return () => {
      if (this.workerInterval) clearInterval(this.workerInterval);
    };
  }
}

export const syncEngine = new SyncEngine();

