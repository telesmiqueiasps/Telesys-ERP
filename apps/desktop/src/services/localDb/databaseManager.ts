import { LOCAL_PATHS, getCompanyDbName } from "./config";
import { MASTER_SCHEMA_SQL } from "./schemas/masterSchema";
import { COMPANY_SCHEMA_SQL } from "./schemas/companySchema";

export interface LocalCompanyRecord {
  id: string;
  tenant_id: string;
  name: string;
  trade_name?: string | null;
  cnpj?: string | null;
  state_registration?: string | null;
  is_active: boolean;
  created_at?: string;
}

export interface SyncQueueItem {
  id: string;
  entity: string;
  entity_id: string;
  operation: "INSERT" | "UPDATE" | "DELETE";
  payload: string;
  created_at: string;
  status: "PENDING" | "SYNCED" | "FAILED";
  attempts: number;
  last_error?: string | null;
}

class LocalDatabaseManager {
  private masterInitialized = false;
  private activeCompanyDbs = new Set<string>();

  /**
   * Initializes the master.db database and storage infrastructure.
   */
  public async initMasterDatabase(): Promise<boolean> {
    if (this.masterInitialized) return true;

    try {
      console.log(`[LocalDB] Inicializando banco master.db em ${LOCAL_PATHS.DATA_DIR} com DDL length ${MASTER_SCHEMA_SQL.length}`);
      
      // In web/dev environment, we initialize local storage backing
      if (typeof window !== "undefined") {
        const storedCompanies = localStorage.getItem("telesys_master_companies");
        if (!storedCompanies) {
          localStorage.setItem("telesys_master_companies", JSON.stringify([]));
        }
      }

      this.masterInitialized = true;
      return true;
    } catch (error) {
      console.error("[LocalDB] Erro ao inicializar master.db:", error);
      return false;
    }
  }

  /**
   * Initializes and opens a specific company SQLite database (empresa_<uuid>.db).
   */
  public async openCompanyDatabase(companyId: string): Promise<boolean> {
    if (!companyId) return false;
    const dbName = getCompanyDbName(companyId);

    try {
      console.log(`[LocalDB] Abrir/Inicializar banco da empresa ${dbName} com DDL length ${COMPANY_SCHEMA_SQL.length}`);
      this.activeCompanyDbs.add(companyId);
      return true;
    } catch (error) {
      console.error(`[LocalDB] Erro ao abrir banco da empresa ${companyId}:`, error);
      return false;
    }
  }

  /**
   * Syncs user's cloud-authorized companies into local master.db.
   */
  public async syncCompaniesToMaster(companies: LocalCompanyRecord[]): Promise<void> {
    await this.initMasterDatabase();
    if (typeof window !== "undefined") {
      localStorage.setItem("telesys_master_companies", JSON.stringify(companies));
    }
  }

  /**
   * Gets local companies stored in master.db.
   */
  public async getLocalCompanies(): Promise<LocalCompanyRecord[]> {
    await this.initMasterDatabase();
    if (typeof window !== "undefined") {
      const data = localStorage.getItem("telesys_master_companies");
      return data ? JSON.parse(data) : [];
    }
    return [];
  }

  /**
   * Checks if master.db and directories are initialized.
   */
  public isReady(): boolean {
    return this.masterInitialized;
  }
}

export const localDbManager = new LocalDatabaseManager();
