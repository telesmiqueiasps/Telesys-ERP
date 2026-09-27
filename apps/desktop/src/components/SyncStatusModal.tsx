import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Wifi,
  WifiOff,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Clock,
  Trash2,
  Database,
  Cloud,
  X,
} from "lucide-react";
import { syncEngine } from "@/services/syncEngine";
import { SyncQueueItem, SyncStatusStats } from "@/types/sync";

interface SyncStatusModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SyncStatusModal({ isOpen, onClose }: SyncStatusModalProps) {
  const [stats, setStats] = useState<SyncStatusStats>(syncEngine.getStats());
  const [queue, setQueue] = useState<SyncQueueItem[]>(syncEngine.getQueue());
  const [isSyncingManual, setIsSyncingManual] = useState(false);

  useEffect(() => {
    if (!isOpen) return;

    const unsubscribe = syncEngine.subscribe((newStats) => {
      setStats(newStats);
      setQueue(syncEngine.getQueue());
    });

    return () => unsubscribe();
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSyncNow = async () => {
    setIsSyncingManual(true);
    await syncEngine.checkApiHealth();
    await syncEngine.pushPendingBatch();
    setStats(syncEngine.getStats());
    setQueue(syncEngine.getQueue());
    setIsSyncingManual(false);
  };

  const handleClearSynced = () => {
    syncEngine.clearSynced();
    setQueue(syncEngine.getQueue());
    setStats(syncEngine.getStats());
  };

  const formatEntityLabel = (entity: string) => {
    switch (entity) {
      case "sale":
        return "Venda PDV";
      case "customer":
        return "Cliente";
      case "stock_movement":
        return "Movimentação Estoque";
      case "cash_movement":
        return "Movimentação Caixa";
      case "product":
        return "Produto";
      default:
        return entity;
    }
  };

  const getStatusBadge = (status: SyncQueueItem["status"]) => {
    switch (status) {
      case "PENDING":
        return (
          <Badge variant="outline" className="gap-1 border-amber-500/40 text-amber-500 bg-amber-500/10">
            <Clock className="h-3 w-3" /> Pendente
          </Badge>
        );
      case "SYNCING":
        return (
          <Badge variant="outline" className="gap-1 border-blue-500/40 text-blue-500 bg-blue-500/10 animate-pulse">
            <RefreshCw className="h-3 w-3 animate-spin" /> Processando
          </Badge>
        );
      case "SYNCED":
        return (
          <Badge variant="success" className="gap-1">
            <CheckCircle2 className="h-3 w-3" /> Sincronizado
          </Badge>
        );
      case "FAILED":
        return (
          <Badge variant="destructive" className="gap-1">
            <AlertCircle className="h-3 w-3" /> Erro
          </Badge>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-3xl overflow-hidden animate-in fade-in zoom-in duration-200 flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-muted/40">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold">
              <Database className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-foreground">Central SyncQueue Local-First</h2>
              <p className="text-xs text-muted-foreground">
                Arquitetura de Sincronização em Segundo Plano (SQLite / Cloud PostgreSQL)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {stats.isOnline ? (
              <Badge variant="success" className="gap-1.5 px-3 py-1 text-xs">
                <Wifi className="h-3.5 w-3.5" /> Online (Cloud Conectado)
              </Badge>
            ) : (
              <Badge variant="destructive" className="gap-1.5 px-3 py-1 text-xs">
                <WifiOff className="h-3.5 w-3.5" /> Offline (Modo Local)
              </Badge>
            )}

            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
              onClick={onClose}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-4 overflow-y-auto flex-1">
          {/* Summary Cards */}
          <div className="grid grid-cols-4 gap-3">
            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 flex flex-col">
              <span className="text-xs text-amber-600 dark:text-amber-400 font-semibold">Pendentes</span>
              <span className="text-2xl font-bold text-amber-600 dark:text-amber-400 mt-1">
                {stats.pendingCount}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 flex flex-col">
              <span className="text-xs text-blue-600 dark:text-blue-400 font-semibold">Em Envio</span>
              <span className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">
                {stats.syncingCount}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex flex-col">
              <span className="text-xs text-emerald-600 dark:text-emerald-400 font-semibold">Sincronizados</span>
              <span className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
                {stats.syncedCount}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 flex flex-col">
              <span className="text-xs text-rose-600 dark:text-rose-400 font-semibold">Falhas</span>
              <span className="text-2xl font-bold text-rose-600 dark:text-rose-400 mt-1">
                {stats.failedCount}
              </span>
            </div>
          </div>

          {/* Action Toolbar */}
          <div className="flex items-center justify-between pt-1">
            <div className="text-xs text-muted-foreground">
              {stats.lastSyncAt ? (
                <span>Última sincronização: {new Date(stats.lastSyncAt).toLocaleTimeString("pt-BR")}</span>
              ) : (
                <span>Nenhuma sincronização recente</span>
              )}
            </div>

            <div className="flex items-center gap-2">
              {stats.syncedCount > 0 && (
                <Button variant="outline" size="sm" onClick={handleClearSynced} className="gap-1.5 text-xs">
                  <Trash2 className="h-3.5 w-3.5 text-muted-foreground" /> Limpar Concluídos
                </Button>
              )}

              <Button
                variant="default"
                size="sm"
                onClick={handleSyncNow}
                disabled={isSyncingManual || (!stats.isOnline && stats.pendingCount === 0)}
                className="gap-1.5 text-xs bg-primary hover:bg-primary/90"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${isSyncingManual ? "animate-spin" : ""}`} />
                {isSyncingManual ? "Sincronizando..." : "Sincronizar Agora"}
              </Button>
            </div>
          </div>

          {/* Queue Events Table */}
          <div className="border border-border rounded-lg max-h-[300px] overflow-y-auto">
            {queue.length === 0 ? (
              <div className="p-8 text-center flex flex-col items-center justify-center space-y-2 text-muted-foreground">
                <Cloud className="h-10 w-10 text-emerald-500/60" />
                <p className="text-sm font-semibold text-foreground">Fila de Eventos Vazia</p>
                <p className="text-xs max-w-sm">
                  Todos os registros locais (vendas, caixa, clientes) estão 100% sincronizados com a nuvem.
                </p>
              </div>
            ) : (
              <table className="w-full text-xs text-left">
                <thead className="bg-muted/60 text-muted-foreground sticky top-0 font-medium">
                  <tr>
                    <th className="p-2.5">Horário</th>
                    <th className="p-2.5">Entidade</th>
                    <th className="p-2.5">Ação</th>
                    <th className="p-2.5">Status</th>
                    <th className="p-2.5">Tentativas</th>
                    <th className="p-2.5">Detalhes / Mensagem</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {queue.map((item) => (
                    <tr key={item.id} className="hover:bg-muted/30 transition-colors">
                      <td className="p-2.5 text-muted-foreground font-mono">
                        {new Date(item.created_at).toLocaleTimeString("pt-BR")}
                      </td>
                      <td className="p-2.5 font-medium">{formatEntityLabel(item.entity_type)}</td>
                      <td className="p-2.5">
                        <span className="font-mono bg-muted px-1.5 py-0.5 rounded text-[10px]">
                          {item.action}
                        </span>
                      </td>
                      <td className="p-2.5">{getStatusBadge(item.status)}</td>
                      <td className="p-2.5 font-mono text-center">{item.attempts}</td>
                      <td className="p-2.5 text-muted-foreground max-w-xs truncate">
                        {item.last_error ? (
                          <span className="text-rose-500 font-medium">{item.last_error}</span>
                        ) : item.synced_at ? (
                          "Processado com sucesso"
                        ) : (
                          "Aguardando envio..."
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
