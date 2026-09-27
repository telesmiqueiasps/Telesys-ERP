import React, { useState, useEffect } from "react";
import { X, CheckCircle2, AlertCircle, DollarSign, CreditCard, Banknote, QrCode } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AccountPayable, AccountReceivable } from "@/types/finance";
import { financeService } from "@/services/financeService";

interface PayOffModalProps {
  isOpen: boolean;
  type: "PAYABLE" | "RECEIVABLE";
  item: AccountPayable | AccountReceivable | null;
  onClose: () => void;
  onSuccess: () => void;
}

export function PayOffModal({ isOpen, type, item, onClose, onSuccess }: PayOffModalProps) {
  const [payAmount, setPayAmount] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("PIX");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !item) return;

    const remaining =
      type === "PAYABLE"
        ? (item as AccountPayable).amount - (item as AccountPayable).paid_amount
        : (item as AccountReceivable).amount - (item as AccountReceivable).received_amount;

    setPayAmount(remaining.toFixed(2));
    setPaymentMethod("PIX");
    setError(null);
  }, [isOpen, item, type]);

  if (!isOpen || !item) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const num = parseFloat(payAmount);
    if (isNaN(num) || num <= 0) {
      setError("Informe um valor de liquidação válido maior que zero.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      if (type === "PAYABLE") {
        await financeService.payAccountPayable(item.id, num, paymentMethod);
      } else {
        await financeService.receiveAccountReceivable(item.id, num, paymentMethod);
      }
      onSuccess();
      onClose();
    } catch (err: any) {
      console.error("Erro ao liquidar título:", err);
      setError(err?.message || "Falha ao dar baixa no título.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-sm overflow-hidden animate-in fade-in zoom-in duration-200">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-muted/40">
          <div className="flex items-center gap-3">
            <div
              className={`h-9 w-9 rounded-lg flex items-center justify-center font-bold ${
                type === "PAYABLE" ? "bg-rose-500/10 text-rose-500" : "bg-emerald-500/10 text-emerald-500"
              }`}
            >
              <DollarSign className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-foreground">
                {type === "PAYABLE" ? "Baixar Conta a Pagar" : "Baixar Conta a Receber"}
              </h2>
              <p className="text-xs text-muted-foreground truncate max-w-[200px]">{item.description}</p>
            </div>
          </div>
          <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-foreground" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-xs flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="p-3 bg-muted/40 rounded-lg border border-border space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Valor Total do Título:</span>
              <span className="font-mono font-bold">R$ {item.amount.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-muted-foreground">
              <span>{type === "PAYABLE" ? "Já Pago:" : "Já Recebido:"}</span>
              <span className="font-mono">
                R$ {type === "PAYABLE" ? (item as AccountPayable).paid_amount.toFixed(2) : (item as AccountReceivable).received_amount.toFixed(2)}
              </span>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-foreground mb-1 block">
              {type === "PAYABLE" ? "Valor a Pagar Agora (R$)" : "Valor a Receber Agora (R$)"} *
            </label>
            <Input
              type="number"
              step="0.01"
              min="0.01"
              value={payAmount}
              onChange={(e) => setPayAmount(e.target.value)}
              className="h-9 text-xs font-mono font-bold"
              required
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-foreground mb-1 block">Forma de Pagamento *</label>
            <div className="grid grid-cols-2 gap-2">
              {[
                { id: "PIX", label: "PIX", icon: QrCode },
                { id: "MONEY", label: "Dinheiro", icon: Banknote },
                { id: "CREDIT_CARD", label: "Cartão Crédito", icon: CreditCard },
                { id: "BOLETO", label: "Boleto", icon: DollarSign },
              ].map((m) => {
                const Icon = m.icon;
                const isSelected = paymentMethod === m.id;
                return (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => setPaymentMethod(m.id)}
                    className={`p-2 rounded-lg border text-xs font-medium flex items-center gap-2 transition-colors ${
                      isSelected
                        ? "border-primary bg-primary/10 text-primary font-bold"
                        : "border-border hover:bg-muted text-muted-foreground"
                    }`}
                  >
                    <Icon className="h-4 w-4" /> {m.label}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="pt-2 flex items-center justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose} className="h-9 text-xs">
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={loading}
              className={`h-9 text-xs gap-1.5 font-bold ${
                type === "PAYABLE" ? "bg-rose-600 hover:bg-rose-700 text-white" : "bg-emerald-600 hover:bg-emerald-700 text-white"
              }`}
            >
              <CheckCircle2 className="h-4 w-4" />
              {loading ? "Confirmando..." : "Confirmar Liquidação"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
