import React, { useState, useEffect, useRef } from "react";
import { X, CheckCircle2, Trash2, CreditCard, Banknote, QrCode, CreditCard as CardIcon, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { CartItem, SaleDetail, SalePaymentInput } from "@/types/sale";
import { Customer } from "@/types/customer";
import { saleService } from "@/services/saleService";
import { syncEngine } from "@/services/syncEngine";
import { useAuthStore } from "@/store/useAuthStore";

interface PaymentModalProps {
  isOpen: boolean;
  subtotal: number;
  cartItems: CartItem[];
  customer?: Customer | null;
  onClose: () => void;
  onSuccess: (sale: SaleDetail) => void;
}

export function PaymentModal({
  isOpen,
  subtotal,
  cartItems,
  customer,
  onClose,
  onSuccess,
}: PaymentModalProps) {
  const { activeCompany } = useAuthStore();
  const [discountAmount, setDiscountAmount] = useState<string>("0.00");
  const [payments, setPayments] = useState<SalePaymentInput[]>([
    { payment_method: "MONEY", amount: 0, change_amount: 0 },
  ]);
  const [receivedCashAmount, setReceivedCashAmount] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cashInputRef = useRef<HTMLInputElement>(null);

  const numDiscount = parseFloat(discountAmount.replace(",", ".")) || 0;
  const finalTotal = Math.max(0, subtotal - numDiscount);

  // Quick Payment Options mapping
  const paymentOptions = [
    { key: "1", code: "MONEY", label: "Dinheiro", icon: Banknote },
    { key: "2", code: "PIX", label: "PIX", icon: QrCode },
    { key: "3", code: "CREDIT_CARD", label: "Crédito", icon: CardIcon },
    { key: "4", code: "DEBIT_CARD", label: "Débito", icon: CreditCard },
    { key: "5", code: "BOLETO", label: "Boleto", icon: FileText },
  ];

  // Reset when opening
  useEffect(() => {
    if (isOpen) {
      setDiscountAmount("0.00");
      setPayments([{ payment_method: "MONEY", amount: finalTotal, change_amount: 0 }]);
      setReceivedCashAmount(finalTotal > 0 ? finalTotal.toFixed(2) : "0.00");
      setError(null);
      setTimeout(() => {
        if (cashInputRef.current) cashInputRef.current.select();
      }, 100);
    }
  }, [isOpen, finalTotal]);

  const selectSinglePaymentMethod = (methodCode: string) => {
    setPayments([{ payment_method: methodCode, amount: finalTotal, change_amount: 0 }]);
    if (methodCode === "MONEY" && cashInputRef.current) {
      cashInputRef.current.focus();
      cashInputRef.current.select();
    }
  };

  // Keyboard shortcut listener for keys 1, 2, 3, 4, 5
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if user is currently typing in an input field (unless they press Number while focused elsewhere)
      const target = e.target as HTMLElement;
      const isInput = target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.tagName === "SELECT";

      if (!isInput) {
        if (e.key === "1") selectSinglePaymentMethod("MONEY");
        else if (e.key === "2") selectSinglePaymentMethod("PIX");
        else if (e.key === "3") selectSinglePaymentMethod("CREDIT_CARD");
        else if (e.key === "4") selectSinglePaymentMethod("DEBIT_CARD");
        else if (e.key === "5") selectSinglePaymentMethod("BOLETO");
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, finalTotal]);

  if (!isOpen) return null;

  const totalPaid = payments.reduce((acc, p) => acc + p.amount, 0);
  const remaining = Math.max(0, finalTotal - totalPaid);

  // Troco
  const cashPayment = payments.find((p) => p.payment_method === "MONEY");
  const numReceivedCash = parseFloat(receivedCashAmount.replace(",", ".")) || 0;
  const changeCalculated =
    cashPayment && numReceivedCash > cashPayment.amount
      ? numReceivedCash - cashPayment.amount
      : 0;

  const handleAddPayment = (method: string) => {
    if (remaining <= 0) return;
    setPayments([...payments, { payment_method: method, amount: remaining, change_amount: 0 }]);
  };

  const handleRemovePayment = (index: number) => {
    if (payments.length <= 1) return;
    setPayments(payments.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    if (cartItems.length === 0) {
      setError("O carrinho não possui itens.");
      return;
    }

    if (totalPaid < finalTotal - 0.01) {
      setError(`O valor total pago (R$ ${totalPaid.toFixed(2)}) é inferior ao total da venda (R$ ${finalTotal.toFixed(2)}).`);
      return;
    }

    setLoading(true);
    setError(null);

    const finalPayments = payments.map((p) => {
      if (p.payment_method === "MONEY") {
        return { ...p, change_amount: changeCalculated };
      }
      return p;
    });

    try {
      const sale = await saleService.createSale(
        {
          customer_id: customer?.id || null,
          items: cartItems.map((item) => ({
            product_id: item.id,
            quantity: item.quantity,
            unit_price: item.unit_price,
            discount_amount: item.discount_amount,
          })),
          payments: finalPayments,
          discount_amount: numDiscount,
        },
        activeCompany?.id
      );

      // Registrar evento na sync engine local-first
      const user = useAuthStore.getState().user;
      if (user && activeCompany) {
        syncEngine.enqueueEvent({
          tenant_id: user.tenant_id,
          company_id: activeCompany.id,
          entity_type: "sale",
          action: "CREATE",
          payload: {
            sale_id: sale.id,
            total_amount: sale.total_amount,
            subtotal: sale.subtotal,
            discount_amount: sale.discount_amount,
            payments_count: sale.payments?.length || 1,
            items_count: sale.items?.length || cartItems.length,
          },
        });
      }

      onSuccess(sale);
      onClose();
    } catch (err: any) {
      console.error("Erro ao finalizar venda:", err);
      setError(err?.message || "Falha ao finalizar venda.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-xl overflow-hidden animate-in fade-in zoom-in duration-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-muted/40">
          <div className="flex items-center gap-2">
            <CreditCard className="h-5 w-5 text-emerald-500" />
            <h2 className="text-lg font-bold">Finalizar Venda & Pagamento</h2>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8 text-muted-foreground">
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 max-h-[80vh] overflow-y-auto">
          {error && (
            <div className="p-3 text-xs bg-destructive/10 border border-destructive/20 text-destructive rounded-lg font-medium">
              {error}
            </div>
          )}

          {/* Totals Summary */}
          <div className="grid grid-cols-3 gap-3 bg-muted/40 p-4 rounded-xl border border-border/60 text-center">
            <div>
              <span className="text-[11px] text-muted-foreground font-semibold uppercase">Subtotal</span>
              <div className="text-lg font-bold font-mono">
                R$ {subtotal.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </div>
            </div>

            <div>
              <span className="text-[11px] text-muted-foreground font-semibold uppercase">Desconto Geral</span>
              <div className="relative mt-1">
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  value={discountAmount}
                  onChange={(e) => setDiscountAmount(e.target.value)}
                  className="h-8 text-xs font-mono font-bold text-center"
                />
              </div>
            </div>

            <div>
              <span className="text-[11px] text-emerald-500 font-semibold uppercase">Total a Pagar</span>
              <div className="text-xl font-extrabold font-mono text-emerald-500">
                R$ {finalTotal.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </div>
            </div>
          </div>

          {/* Seleção Numérica de Forma de Pagamento (Atalhos 1 a 5) */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-muted-foreground">
                Selecione a Forma de Pagamento (Teclas 1 a 5)
              </label>
              <span className="text-[10px] text-muted-foreground italic">Pressione o número no teclado</span>
            </div>
            
            <div className="grid grid-cols-5 gap-2">
              {paymentOptions.map((opt) => {
                const Icon = opt.icon;
                const isSelected = payments.length === 1 && payments[0].payment_method === opt.code;
                return (
                  <button
                    key={opt.code}
                    type="button"
                    onClick={() => selectSinglePaymentMethod(opt.code)}
                    className={`flex flex-col items-center justify-center p-2.5 rounded-xl border text-xs font-semibold transition-all relative group ${
                      isSelected
                        ? "bg-primary text-primary-foreground border-primary shadow-md ring-2 ring-primary/30"
                        : "bg-card border-border hover:bg-accent text-foreground"
                    }`}
                  >
                    <span className="absolute top-1 left-1.5 font-mono text-[10px] font-bold opacity-70 bg-black/10 dark:bg-white/10 px-1 rounded">
                      [{opt.key}]
                    </span>
                    <Icon className="h-5 w-5 mb-1 text-emerald-500" />
                    <span className="text-[11px] font-bold">{opt.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Active Payments List */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-muted-foreground">Pagamentos Lançados</label>
              <div className="flex items-center gap-2">
                {remaining > 0 && (
                  <span className="text-xs text-amber-500 font-bold">
                    Restante: R$ {remaining.toFixed(2)}
                  </span>
                )}
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => handleAddPayment("MONEY")}
                  className="h-6 text-[11px] font-semibold text-primary"
                >
                  + Dividir Pagamento
                </Button>
              </div>
            </div>

            {payments.map((p, idx) => (
              <div key={idx} className="flex items-center gap-3 p-2 bg-card border border-border/80 rounded-lg">
                <select
                  value={p.payment_method}
                  onChange={(e) => {
                    const newP = [...payments];
                    newP[idx].payment_method = e.target.value;
                    setPayments(newP);
                  }}
                  className="h-9 px-2 text-xs rounded border border-input bg-background font-semibold"
                >
                  <option value="MONEY">Dinheiro [1]</option>
                  <option value="PIX">PIX [2]</option>
                  <option value="CREDIT_CARD">Cartão de Crédito [3]</option>
                  <option value="DEBIT_CARD">Cartão de Débito [4]</option>
                  <option value="BOLETO">Boleto [5]</option>
                </select>

                <div className="flex-1 relative">
                  <span className="absolute left-2.5 top-2 text-xs font-bold text-muted-foreground">R$</span>
                  <Input
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={p.amount}
                    onChange={(e) => {
                      const newP = [...payments];
                      newP[idx].amount = parseFloat(e.target.value) || 0;
                      setPayments(newP);
                    }}
                    className="pl-8 h-9 text-xs font-mono font-bold"
                  />
                </div>

                {payments.length > 1 && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => handleRemovePayment(idx)}
                    className="h-8 w-8 text-destructive hover:bg-destructive/10"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </div>
            ))}
          </div>

          {/* Cash Change Calculation if Money is selected */}
          {payments.some((p) => p.payment_method === "MONEY") && (
            <div className="p-3.5 bg-muted/40 rounded-xl border border-border/60 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-muted-foreground">Valor Recebido em Dinheiro (R$):</span>
                <div className="w-36 relative">
                  <span className="absolute left-2.5 top-1.5 text-xs font-bold text-muted-foreground">R$</span>
                  <Input
                    ref={cashInputRef}
                    type="number"
                    step="0.01"
                    value={receivedCashAmount}
                    onChange={(e) => setReceivedCashAmount(e.target.value)}
                    className="pl-8 h-9 text-xs font-mono font-bold text-emerald-500"
                  />
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-border/60">
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-500">Troco a Devolver:</span>
                <span className="font-mono font-extrabold text-lg text-emerald-500">
                  R$ {changeCalculated.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                </span>
              </div>
            </div>
          )}

          {/* Footer Actions */}
          <div className="pt-4 border-t border-border flex items-center justify-between">
            <Button type="button" variant="outline" onClick={onClose} disabled={loading}>
              Voltar (Esc)
            </Button>
            <Button
              type="submit"
              disabled={loading}
              className="gap-2 font-bold bg-emerald-600 hover:bg-emerald-700 text-white h-11 px-6 shadow-md"
            >
              <CheckCircle2 className="h-5 w-5" />
              {loading ? "Finalizando..." : "Concluir Venda (Enter)"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
