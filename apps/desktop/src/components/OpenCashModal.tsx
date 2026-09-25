import React, { useState } from "react";
import { X, DollarSign, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cashService } from "@/services/cashService";
import { useAuthStore } from "@/store/useAuthStore";

interface OpenCashModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function OpenCashModal({ isOpen, onClose, onSuccess }: OpenCashModalProps) {
  const { activeCompany } = useAuthStore();
  const [initialBalance, setInitialBalance] = useState<string>("0.00");
  const [notes, setNotes] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const val = parseFloat(initialBalance.replace(",", "."));
    if (isNaN(val) || val < 0) {
      setError("Informe um valor válido para o fundo de troco inicial.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await cashService.openCash(
        {
          initial_balance: val,
          notes: notes.trim() || undefined,
        },
        activeCompany?.id
      );
      onSuccess();
      onClose();
    } catch (err: any) {
      console.error("Erro ao abrir caixa:", err);
      setError(err?.message || "Falha ao abrir o caixa.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-muted/40">
          <div className="flex items-center gap-2">
            <DollarSign className="h-5 w-5 text-emerald-500" />
            <h2 className="text-lg font-bold">Abertura de Caixa</h2>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8 text-muted-foreground">
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 text-xs bg-destructive/10 border border-destructive/20 text-destructive rounded-lg font-medium">
              {error}
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground">
              Fundo de Troco (Valor Inicial em Dinheiro) *
            </label>
            <div className="relative">
              <span className="absolute left-3 top-2.5 text-xs font-bold text-muted-foreground">R$</span>
              <Input
                type="number"
                step="0.01"
                min="0"
                value={initialBalance}
                onChange={(e) => setInitialBalance(e.target.value)}
                placeholder="0.00"
                className="pl-9 font-mono font-bold text-base"
                required
                autoFocus
              />
            </div>
            <p className="text-[11px] text-muted-foreground">
              Valor físico disponível na gaveta para iniciar a operação.
            </p>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground">Observações de Abertura</label>
            <Input
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Ex: Troco inicial conferido por Maria"
            />
          </div>

          {/* Footer Actions */}
          <div className="pt-4 border-t border-border flex items-center justify-end gap-3">
            <Button type="button" variant="outline" onClick={onClose} disabled={loading}>
              Cancelar
            </Button>
            <Button type="submit" disabled={loading} className="gap-2 font-semibold bg-emerald-600 hover:bg-emerald-700">
              <CheckCircle2 className="h-4 w-4" />
              {loading ? "Abrindo..." : "Confirmar Abertura"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
