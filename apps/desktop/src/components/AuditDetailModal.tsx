import { X, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AuditLogItem } from "@/types/audit";

interface AuditDetailModalProps {
  isOpen: boolean;
  log: AuditLogItem | null;
  onClose: () => void;
}

export function AuditDetailModal({ isOpen, log, onClose }: AuditDetailModalProps) {
  if (!isOpen || !log) return null;

  const formatJson = (dataStr?: string | null) => {
    if (!dataStr) return null;
    try {
      const parsed = JSON.parse(dataStr);
      return JSON.stringify(parsed, null, 2);
    } catch {
      return dataStr;
    }
  };

  const beforeFormatted = formatJson(log.before_data);
  const afterFormatted = formatJson(log.after_data);

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-2xl overflow-hidden animate-in fade-in zoom-in duration-200 flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-muted/40">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-foreground">Registro de Auditoria #{log.id.slice(-6)}</h2>
              <p className="text-xs text-muted-foreground">
                Rastreabilidade de alteração no módulo <span className="font-semibold">{log.entity}</span>
              </p>
            </div>
          </div>

          <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-foreground" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4 overflow-y-auto flex-1">
          {/* Metadata Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-3 bg-muted/30 border border-border rounded-lg text-xs">
            <div>
              <span className="text-muted-foreground block">Operador / Usuário:</span>
              <span className="font-semibold text-foreground">{log.user_name || "Sistema"}</span>
            </div>

            <div>
              <span className="text-muted-foreground block">Módulo / Entidade:</span>
              <span className="font-semibold text-foreground uppercase">{log.entity}</span>
            </div>

            <div>
              <span className="text-muted-foreground block">Tipo de Ação:</span>
              <Badge variant="outline" className="font-mono mt-0.5">
                {log.action}
              </Badge>
            </div>

            <div>
              <span className="text-muted-foreground block">Data & Hora:</span>
              <span className="font-mono text-muted-foreground">
                {new Date(log.created_at).toLocaleString("pt-BR")}
              </span>
            </div>
          </div>

          {/* Diff Section */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Before Data */}
            <div className="space-y-1">
              <span className="text-xs font-bold text-rose-600 dark:text-rose-400 block">Estado Anterior (Before):</span>
              <div className="p-3 bg-muted/50 border border-border rounded-lg font-mono text-[11px] text-muted-foreground max-h-60 overflow-y-auto whitespace-pre-wrap">
                {beforeFormatted ? (
                  beforeFormatted
                ) : (
                  <span className="italic text-muted-foreground/60">Nenhum dado anterior (Criação de registro)</span>
                )}
              </div>
            </div>

            {/* After Data */}
            <div className="space-y-1">
              <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 block">Novo Estado (After):</span>
              <div className="p-3 bg-muted/50 border border-border rounded-lg font-mono text-[11px] text-foreground max-h-60 overflow-y-auto whitespace-pre-wrap">
                {afterFormatted ? (
                  afterFormatted
                ) : (
                  <span className="italic text-muted-foreground/60">Nenhum dado novo (Exclusão de registro)</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
