import React, { useState } from "react";
import { X, ArrowDownRight, ArrowUpRight, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cashService } from "@/services/cashService";
import { useAuthStore } from "@/store/useAuthStore";
import { PaymentMethod } from "@/types/cash";

interface CashMovementModalProps {
  isOpen: boolean;
  type: "SUPPLY" | "BLEED";
  onClose: () => void;
  onSuccess: () => void;
}

export function CashMovementModal({ isOpen, type, onClose, onSuccess }: CashMovementModalProps) {
  const { activeCompany } = useAuthStore();
  const [amount, setAmount] = useState<string>("");
  const [description, setDescription] = useState<string>("");
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("MONEY");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const isSupply = type === "SUPPLY";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const val = parseFloat(amount.replace(",", "."));
    if (isNaN(val) || val <= 0) {
      setError("Informe um valor maior que zero.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await cashService.createMovement(
        {
          movement_type: type,
          payment_method: paymentMethod,
          amount: val,
          description: description.trim() || (isSupply ? "Suprimento de Caixa" : "Sangria de Caixa"),
        },
        activeCompany?.id
      );
      onSuccess();
      onClose();
    } catch (err: any) {
      console.error("Erro ao registrar movimentação:", err);
      setError(err?.message || "Falha ao registrar movimentação.");
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
            {isSupply ? (
              <ArrowDownRight className="h-5 w-5 text-emerald-500" />
            ) : (
              <ArrowUpRight className="h-5 w-5 text-amber-500" />
            )}
            <h2 className="text-lg font-bold">
              {isSupply ? "Registrar Suprimento (Entrada)" : "Registrar Sangria (Retirada)"}
            </h2>
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
            <label className="text-xs font-semibold text-muted-foreground">Valor *</label>
            <div className="relative">
              <span className="absolute left-3 top-2.5 text-xs font-bold text-muted-foreground">R$</span>
              <Input
                type="number"
                step="0.01"
                min="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                className="pl-9 font-mono font-bold text-base"
                required
                autoFocus
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground">Forma de Pagamento</label>
            <select
              value={paymentMethod}
              onChange={(e) => setPaymentMethod(e.target.value as PaymentMethod)}
              className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="MONEY">Dinheiro (Espécie)</option>
              <option value="PIX">PIX</option>
              <option value="CREDIT_CARD">Cartão de Crédito</option>
              <option value="DEBIT_CARD">Cartão de Débito</option>
              <option value="OTHER">Outros</option>
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground">Motivo / Descrição *</label>
            <Input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={isSupply ? "Ex: Adição de moedas de troco" : "Ex: Retirada de valor em excesso para o cofre"}
              required
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
              className={`gap-2 font-semibold ${
                isSupply ? "bg-emerald-600 hover:bg-emerald-700" : "bg-amber-600 hover:bg-amber-700"
              }`}
            >
              <CheckCircle2 className="h-4 w-4" />
              {loading ? "Salvando..." : isSupply ? "Confirmar Suprimento" : "Confirmar Sangria"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
