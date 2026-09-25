import React, { useState } from "react";
import { X, Lock, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cashService } from "@/services/cashService";
import { useAuthStore } from "@/store/useAuthStore";
import { CashRegisterDetail } from "@/types/cash";

interface CloseCashModalProps {
  isOpen: boolean;
  currentCash: CashRegisterDetail | null;
  onClose: () => void;
  onSuccess: () => void;
}

export function CloseCashModal({ isOpen, currentCash, onClose, onSuccess }: CloseCashModalProps) {
  const { activeCompany } = useAuthStore();
  const [declaredBalance, setDeclaredBalance] = useState<string>("");
  const [notes, setNotes] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen || !currentCash) return null;

  const currentBalance = currentCash.current_balance || 0;
  const numDeclared = parseFloat(declaredBalance.replace(",", ".")) || 0;
  const diff = numDeclared - currentBalance;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!declaredBalance.trim()) {
      setError("Informe o valor apurado na contagem do caixa.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await cashService.closeCash(
        {
          final_declared_balance: numDeclared,
          notes: notes.trim() || undefined,
        },
        activeCompany?.id
      );
      onSuccess();
      onClose();
    } catch (err: any) {
      console.error("Erro ao fechar caixa:", err);
      setError(err?.message || "Falha ao fechar caixa.");
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
            <Lock className="h-5 w-5 text-destructive" />
            <h2 className="text-lg font-bold">Fechamento de Caixa</h2>
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

          {/* Balance summary */}
          <div className="p-3 bg-muted/50 rounded-lg border border-border/60 space-y-1">
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Saldo Calculado no Sistema:</span>
              <span className="font-mono font-bold text-foreground">
                R$ {currentBalance.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </span>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground">
              Valor Contado / Declarado na Gaveta (Dinheiro) *
            </label>
            <div className="relative">
              <span className="absolute left-3 top-2.5 text-xs font-bold text-muted-foreground">R$</span>
              <Input
                type="number"
                step="0.01"
                min="0"
                value={declaredBalance}
                onChange={(e) => setDeclaredBalance(e.target.value)}
                placeholder="0.00"
                className="pl-9 font-mono font-bold text-base"
                required
                autoFocus
              />
            </div>
          </div>

          {/* Divergence calculation preview */}
          {declaredBalance.trim() !== "" && (
            <div
              className={`p-3 rounded-lg border text-xs font-semibold flex items-center justify-between ${
                diff === 0
                  ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-500"
                  : diff > 0
                  ? "bg-blue-500/10 border-blue-500/20 text-blue-500"
                  : "bg-amber-500/10 border-amber-500/20 text-amber-500"
              }`}
            >
              <span className="flex items-center gap-1">
                {diff !== 0 && <AlertTriangle className="h-3.5 w-3.5" />}
                {diff === 0
                  ? "Conferência exata (Sem divergência)"
                  : diff > 0
                  ? "Sobra de Caixa"
                  : "Falta de Caixa"}
              </span>
              <span className="font-mono font-bold">
                {diff > 0 ? "+" : ""} R$ {diff.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </span>
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground">Observações do Fechamento</label>
            <Input
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Ex: Motivo da falta/sobra ou observações de encerramento"
            />
          </div>

          {/* Footer Actions */}
          <div className="pt-4 border-t border-border flex items-center justify-end gap-3">
            <Button type="button" variant="outline" onClick={onClose} disabled={loading}>
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={loading}
              className="gap-2 font-semibold bg-destructive hover:bg-destructive/90 text-destructive-foreground"
            >
              <Lock className="h-4 w-4" />
              {loading ? "Encerrando..." : "Confirmar Fechamento"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
