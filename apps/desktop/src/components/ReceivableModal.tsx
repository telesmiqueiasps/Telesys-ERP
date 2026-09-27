import React, { useState, useEffect } from "react";
import { X, DollarSign, AlertCircle, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Customer } from "@/types/customer";
import { FinancialCategory, AccountReceivable } from "@/types/finance";
import { financeService } from "@/services/financeService";
import { customerService } from "@/services/customerService";
import { useAuthStore } from "@/store/useAuthStore";

interface ReceivableModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (receivable: AccountReceivable) => void;
}

export function ReceivableModal({ isOpen, onClose, onSuccess }: ReceivableModalProps) {
  const { activeCompany } = useAuthStore();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [categories, setCategories] = useState<FinancialCategory[]>([]);

  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [dueDate, setDueDate] = useState(new Date().toISOString().split("T")[0]);
  const [customerId, setCustomerId] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [notes, setNotes] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !activeCompany) return;

    const fetchData = async () => {
      try {
        const [custList, catList] = await Promise.all([
          customerService.getCustomers(activeCompany.id),
          financeService.getCategories(activeCompany.id),
        ]);
        setCustomers(custList);
        setCategories(catList.filter((c) => c.type === "RECEITA"));
      } catch (err) {
        console.error("Erro ao carregar dados do modal de conta a receber:", err);
      }
    };

    fetchData();
    setDescription("");
    setAmount("");
    setDueDate(new Date().toISOString().split("T")[0]);
    setCustomerId("");
    setCategoryId("");
    setNotes("");
    setError(null);
  }, [isOpen, activeCompany]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) {
      setError("Informe a descrição do título.");
      return;
    }
    const numAmount = parseFloat(amount);
    if (isNaN(numAmount) || numAmount <= 0) {
      setError("Informe um valor válido maior que zero.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const receivable = await financeService.createReceivable(
        {
          description: description.trim(),
          amount: numAmount,
          due_date: dueDate,
          customer_id: customerId || null,
          category_id: categoryId || null,
          notes: notes.trim() || undefined,
        },
        activeCompany?.id
      );

      onSuccess(receivable);
      onClose();
    } catch (err: any) {
      console.error("Erro ao cadastrar conta a receber:", err);
      setError(err?.message || "Falha ao cadastrar conta a receber.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-muted/40">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-emerald-500/10 text-emerald-500 flex items-center justify-center font-bold">
              <DollarSign className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-foreground">Nova Conta a Receber</h2>
              <p className="text-xs text-muted-foreground">Lançamento de receita ou venda a prazo</p>
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

          <div>
            <label className="text-xs font-semibold text-foreground mb-1 block">Descrição do Título *</label>
            <Input
              placeholder="Ex: Venda Faturada, Prestação de Serviços..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="h-9 text-xs"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-foreground mb-1 block">Valor (R$) *</label>
              <Input
                type="number"
                step="0.01"
                min="0.01"
                placeholder="0.00"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="h-9 text-xs font-mono font-bold"
                required
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-foreground mb-1 block">Data de Vencimento *</label>
              <Input
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="h-9 text-xs font-mono"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-foreground mb-1 block">Cliente (Opcional)</label>
              <select
                value={customerId}
                onChange={(e) => setCustomerId(e.target.value)}
                className="w-full h-9 rounded-md border border-input bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="">Selecione o Cliente...</option>
                {customers.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-foreground mb-1 block">Categoria Financeira</label>
              <select
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
                className="w-full h-9 rounded-md border border-input bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="">Selecione a Categoria...</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-foreground mb-1 block">Observações</label>
            <Input
              placeholder="Nº do pedido, duplicata ou contrato..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="h-9 text-xs"
            />
          </div>

          <div className="pt-2 flex items-center justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose} className="h-9 text-xs">
              Cancelar
            </Button>
            <Button type="submit" disabled={loading} className="h-9 text-xs gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white">
              <CheckCircle2 className="h-4 w-4" />
              {loading ? "Salvando..." : "Salvar Conta a Receber"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
