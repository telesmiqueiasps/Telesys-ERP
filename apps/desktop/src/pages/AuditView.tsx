import { useState, useEffect } from "react";
import {
  ShieldCheck,
  Search,
  RefreshCw,
  FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { AuditLogItem } from "@/types/audit";
import { auditService } from "@/services/auditService";
import { AuditDetailModal } from "@/components/AuditDetailModal";
import { useAuthStore } from "@/store/useAuthStore";

export function AuditView() {
  const { activeCompany } = useAuthStore();
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedEntity, setSelectedEntity] = useState<string>("ALL");
  const [selectedAction, setSelectedAction] = useState<string>("ALL");
  const [searchTerm, setSearchTerm] = useState<string>("");

  const [selectedLog, setSelectedLog] = useState<AuditLogItem | null>(null);

  const fetchLogs = async () => {
    if (!activeCompany) return;
    setLoading(true);
    try {
      const data = await auditService.getAuditLogs(activeCompany.id, {
        entity: selectedEntity !== "ALL" ? selectedEntity : undefined,
        action: selectedAction !== "ALL" ? selectedAction : undefined,
        limit: 150,
      });
      setLogs(data);
    } catch (err) {
      console.error("Erro ao carregar logs de auditoria:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [activeCompany, selectedEntity, selectedAction]);

  const filteredLogs = logs.filter((log) => {
    const matchesSearch =
      (log.user_name && log.user_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.entity.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (log.after_data && log.after_data.toLowerCase().includes(searchTerm.toLowerCase()));

    return matchesSearch;
  });

  const getActionBadge = (action: string) => {
    switch (action) {
      case "CREATE":
        return <Badge variant="success">Criado</Badge>;
      case "UPDATE":
        return <Badge variant="outline" className="border-blue-500/40 text-blue-500 bg-blue-500/10">Atualizado</Badge>;
      case "DELETE":
      case "CANCEL":
        return <Badge variant="destructive">{action === "CANCEL" ? "Cancelado" : "Excluído"}</Badge>;
      case "PRICE_CHANGE":
        return <Badge variant="outline" className="border-amber-500/40 text-amber-500 bg-amber-500/10">Alteração Preço</Badge>;
      case "STOCK_ADJUSTMENT":
        return <Badge variant="outline" className="border-purple-500/40 text-purple-500 bg-purple-500/10">Ajuste Estoque</Badge>;
      default:
        return <Badge variant="outline">{action}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-primary" /> Auditoria & Rastreabilidade de Operações
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Registro imutável de alterações de preços, cancelamentos, fechamento de caixa e permissões
          </p>
        </div>

        <Button variant="outline" size="sm" onClick={fetchLogs} disabled={loading} className="gap-1.5 text-xs h-9">
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          Atualizar Logs
        </Button>
      </div>

      {/* Filter Toolbar */}
      <div className="p-4 bg-card border border-border rounded-xl shadow-sm space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Buscar por operador, ação ou palavra-chave..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 h-9 text-xs"
            />
          </div>

          {/* Module Filter */}
          <div>
            <select
              value={selectedEntity}
              onChange={(e) => setSelectedEntity(e.target.value)}
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="ALL">Todos os Módulos</option>
              <option value="product">Produtos & Estoque</option>
              <option value="sale">Vendas & PDV</option>
              <option value="cash">Caixa & Movimentações</option>
              <option value="purchase">Compras & Entradas</option>
              <option value="finance">Módulo Financeiro</option>
              <option value="user">Usuários & Permissões</option>
            </select>
          </div>

          {/* Action Filter */}
          <div>
            <select
              value={selectedAction}
              onChange={(e) => setSelectedAction(e.target.value)}
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="ALL">Todas as Ações</option>
              <option value="CREATE">Criação (CREATE)</option>
              <option value="UPDATE">Atualização (UPDATE)</option>
              <option value="CANCEL">Cancelamento (CANCEL)</option>
              <option value="PRICE_CHANGE">Alteração de Preço</option>
              <option value="STOCK_ADJUSTMENT">Ajuste de Estoque</option>
            </select>
          </div>
        </div>
      </div>

      {/* Audit Logs Table */}
      <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-muted-foreground flex flex-col items-center justify-center space-y-2">
            <RefreshCw className="h-6 w-6 animate-spin text-primary" />
            <span>Carregando logs de auditoria...</span>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="p-12 text-center text-xs text-muted-foreground flex flex-col items-center justify-center space-y-2">
            <ShieldCheck className="h-10 w-10 text-muted-foreground/50" />
            <span className="font-semibold text-foreground text-sm">Nenhum registro de auditoria encontrado</span>
            <span>As operações sensíveis executadas no sistema aparecerão nesta lista.</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-muted/60 text-muted-foreground border-b border-border font-medium">
                <tr>
                  <th className="p-3">Data / Hora</th>
                  <th className="p-3">Operador</th>
                  <th className="p-3">Módulo / Entidade</th>
                  <th className="p-3">Ação</th>
                  <th className="p-3">ID da Entidade</th>
                  <th className="p-3 text-center">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-muted/30 transition-colors">
                    <td className="p-3 font-mono text-muted-foreground">
                      {new Date(log.created_at).toLocaleString("pt-BR")}
                    </td>
                    <td className="p-3 font-semibold text-foreground">{log.user_name || "Sistema"}</td>
                    <td className="p-3 font-medium uppercase text-muted-foreground">{log.entity}</td>
                    <td className="p-3">{getActionBadge(log.action)}</td>
                    <td className="p-3 font-mono text-muted-foreground text-[11px]">
                      {log.entity_id ? log.entity_id.slice(-8) : "-"}
                    </td>
                    <td className="p-3 text-center">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedLog(log)}
                        className="h-7 text-xs px-2.5 gap-1 text-primary hover:text-primary hover:bg-primary/10"
                      >
                        <FileText className="h-3.5 w-3.5" /> Ver Diff
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal de Detalhes / Diff */}
      <AuditDetailModal
        isOpen={!!selectedLog}
        log={selectedLog}
        onClose={() => setSelectedLog(null)}
      />
    </div>
  );
}
