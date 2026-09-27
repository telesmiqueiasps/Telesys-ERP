import React, { useState, useEffect } from "react";
import { X, DollarSign, AlertCircle, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Supplier } from "@/types/customer";
import { FinancialCategory, AccountPayable } from "@/types/finance";
import { financeService } from "@/services/financeService";
import { customerService } from "@/services/customerService";
import { useAuthStore } from "@/store/useAuthStore";

interface PayableModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (payable: AccountPayable) => void;
}

export function PayableModal({ isOpen, onClose, onSuccess }: PayableModalProps) {
  const { activeCompany } = useAuthStore();
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [categories, setCategories] = useState<FinancialCategory[]>([]);

  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [dueDate, setDueDate] = useState(new Date().toISOString().split("T")[0]);
  const [supplierId, setSupplierId] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [notes, setNotes] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !activeCompany) return;

    const fetchData = async () => {
      try {
        const [suppList, catList] = await Promise.all([
          customerService.getSuppliers(activeCompany.id),
          financeService.getCategories(activeCompany.id),
        ]);
        setSuppliers(suppList);
        setCategories(catList.filter((c) => c.type === "DESPESA"));
      } catch (err) {
        console.error("Erro ao carregar dados do modal de conta a pagar:", err);
      }
    };

    fetchData();
    setDescription("");
    setAmount("");
    setDueDate(new Date().toISOString().split("T")[0]);
    setSupplierId("");
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
      const payable = await financeService.createPayable(
        {
          description: description.trim(),
          amount: numAmount,
          due_date: dueDate,
          supplier_id: supplierId || null,
          category_id: categoryId || null,
          notes: notes.trim() || undefined,
        },
        activeCompany?.id
      );

      onSuccess(payable);
      onClose();
    } catch (err: any) {
      console.error("Erro ao cadastrar conta a pagar:", err);
      setError(err?.message || "Falha ao cadastrar conta a pagar.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-muted/40">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-rose-500/10 text-rose-500 flex items-center justify-center font-bold">
              <DollarSign className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-foreground">Nova Conta a Pagar</h2>
              <p className="text-xs text-muted-foreground">Lançamento de despesa ou fornecedor</p>
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
              placeholder="Ex: Aluguel do Galpão, Compra de Suprimentos..."
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
              <label className="text-xs font-semibold text-foreground mb-1 block">Fornecedor (Opcional)</label>
              <select
                value={supplierId}
                onChange={(e) => setSupplierId(e.target.value)}
                className="w-full h-9 rounded-md border border-input bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="">Selecione o Fornecedor...</option>
                {suppliers.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
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
              placeholder="Nº da fatura, boleto ou nota fiscal..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="h-9 text-xs"
            />
          </div>

          <div className="pt-2 flex items-center justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose} className="h-9 text-xs">
              Cancelar
            </Button>
            <Button type="submit" disabled={loading} className="h-9 text-xs gap-1.5 bg-rose-600 hover:bg-rose-700 text-white">
              <CheckCircle2 className="h-4 w-4" />
              {loading ? "Salvando..." : "Salvar Conta a Pagar"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
