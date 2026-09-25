import { useState, useEffect } from "react";
import { Database, HardDrive, FolderTree, RefreshCw, CheckCircle2, FileCode } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { localDbManager } from "@/services/localDb/databaseManager";
import { LOCAL_PATHS, getCompanyDbName } from "@/services/localDb/config";
import { useAuthStore } from "@/store/useAuthStore";

export function LocalDbStatusCard() {
  const { activeCompany } = useAuthStore();
  const [isInitializing, setIsInitializing] = useState(false);
  const [masterStatus, setMasterStatus] = useState<"READY" | "INITIALIZING" | "IDLE">("IDLE");
  const [companyDbName, setCompanyDbName] = useState<string>("");

  useEffect(() => {
    if (activeCompany) {
      setCompanyDbName(getCompanyDbName(activeCompany.id));
      localDbManager.openCompanyDatabase(activeCompany.id);
    }
  }, [activeCompany]);

  const handleInitDatabase = async () => {
    setIsInitializing(true);
    setMasterStatus("INITIALIZING");
    await localDbManager.initMasterDatabase();
    if (activeCompany) {
      await localDbManager.openCompanyDatabase(activeCompany.id);
    }
    setMasterStatus("READY");
    setIsInitializing(false);
  };

  return (
    <Card className="border-border/60">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-500 border border-amber-500/20">
              <Database className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-base font-bold">Banco de Dados Local (SQLite)</CardTitle>
              <CardDescription className="text-xs">
                Camada local-first `master.db` e `empresa_&lt;uuid&gt;.db` para operação offline do caixa
              </CardDescription>
            </div>
          </div>

          <Badge variant={masterStatus === "READY" ? "success" : "outline"} className="gap-1.5 px-3 py-1">
            <CheckCircle2 className="h-3.5 w-3.5" />
            {masterStatus === "READY" ? "Bancos SQLite Inicializados" : "SQLite Local Pronto"}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Directory Structure Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div className="p-3 rounded-lg bg-muted/40 border space-y-1 font-mono">
            <div className="flex items-center gap-2 text-foreground font-bold font-sans">
              <HardDrive className="h-4 w-4 text-primary" /> Master Database (master.db)
            </div>
            <p className="text-muted-foreground text-[11px] truncate">
              {LOCAL_PATHS.DATA_DIR}\{LOCAL_PATHS.MASTER_DB_NAME}
            </p>
            <div className="text-[10px] text-emerald-600 dark:text-emerald-400">
              ✓ Tabela app_settings, local_companies, local_session
            </div>
          </div>

          <div className="p-3 rounded-lg bg-muted/40 border space-y-1 font-mono">
            <div className="flex items-center gap-2 text-foreground font-bold font-sans">
              <FolderTree className="h-4 w-4 text-emerald-500" /> Banco por Empresa (Empresa Database)
            </div>
            <p className="text-muted-foreground text-[11px] truncate">
              {LOCAL_PATHS.EMPRESAS_DIR}\{companyDbName || "empresa_<uuid>.db"}
            </p>
            <div className="text-[10px] text-emerald-600 dark:text-emerald-400">
              ✓ Tabela sync_queue, local_products, local_sales
            </div>
          </div>
        </div>

        {/* Directory Tree */}
        <div className="p-3.5 rounded-lg bg-slate-900 text-slate-200 text-xs font-mono space-y-1">
          <div className="text-slate-400 font-sans font-bold flex items-center gap-2 mb-2">
            <FileCode className="h-4 w-4 text-blue-400" /> Árvore de Diretórios do Windows (C:\ProgramData\telesys)
          </div>
          <div>C:\ProgramData\telesys\</div>
          <div>├── data\</div>
          <div>│   ├── master.db <span className="text-slate-400">(Configurações e Empresas)</span></div>
          <div>│   └── empresas\</div>
          <div>│       └── {companyDbName || "empresa_<uuid>.db"} <span className="text-emerald-400">(Operação do Caixa)</span></div>
          <div>├── logs\ <span className="text-slate-500">(Auditoria local)</span></div>
          <div>├── cache\ <span className="text-slate-500">(Cache de produtos)</span></div>
          <div>└── config\ <span className="text-slate-500">(Parâmetros de hardware)</span></div>
        </div>

        <div className="flex justify-end pt-1">
          <Button
            size="sm"
            variant="outline"
            className="gap-2 text-xs"
            onClick={handleInitDatabase}
            disabled={isInitializing}
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isInitializing ? "animate-spin" : ""}`} />
            Reinicializar Estrutura SQLite Local
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
