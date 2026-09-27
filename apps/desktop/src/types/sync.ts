export type SyncEventStatus = "PENDING" | "SYNCING" | "SYNCED" | "FAILED";

export type EntityType = "sale" | "customer" | "stock_movement" | "cash_movement" | "product";

export type SyncAction = "CREATE" | "UPDATE" | "DELETE";

export interface SyncQueueItem {
  id: string;
  event_id: string;
  tenant_id: string;
  company_id: string;
  entity_type: EntityType;
  action: SyncAction;
  payload: Record<string, any>;
  status: SyncEventStatus;
  attempts: number;
  last_error?: string | null;
  created_at: string;
  synced_at?: string | null;
}

export interface SyncStatusStats {
  isOnline: boolean;
  pendingCount: number;
  syncingCount: number;
  syncedCount: number;
  failedCount: number;
  lastSyncAt: string | null;
}
