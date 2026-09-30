import { useState, useEffect } from "react";
import {
  DollarSign,
  Plus,
  Search,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ArrowUpRight,
  ArrowDownLeft,
  Tag,
  TrendingUp,
  XCircle,
  Wallet,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  AccountPayable,
  AccountReceivable,
  FinancialCategory,
  FinancialSummary,
} from "@/types/finance";
import { financeService } from "@/services/financeService";
import { PayableModal } from "@/components/PayableModal";
import { ReceivableModal } from "@/components/ReceivableModal";
import { PayOffModal } from "@/components/PayOffModal";
import { CashView } from "@/pages/CashView";
import { useAuthStore } from "@/store/useAuthStore";

export function FinanceView() {
  const { activeCompany } = useAuthStore();
  const [activeTab, setActiveTab] = useState<"caixa" | "payables" | "receivables" | "categories">("payables");

  const [summary, setSummary] = useState<FinancialSummary>({
    total_receivable_pending: 0,
    total_payable_pending: 0,
    total_overdue: 0,
    forecast_balance: 0,
  });

  const [payables, setPayables] = useState<AccountPayable[]>([]);
  const [receivables, setReceivables] = useState<AccountReceivable[]>([]);
  const [categories, setCategories] = useState<FinancialCategory[]>([]);

  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

  // Modais
  const [isPayableModalOpen, setIsPayableModalOpen] = useState(false);
  const [isReceivableModalOpen, setIsReceivableModalOpen] = useState(false);
  const [payOffModalState, setPayOffModalState] = useState<{
    isOpen: boolean;
    type: "PAYABLE" | "RECEIVABLE";
    item: AccountPayable | AccountReceivable | null;
  }>({
    isOpen: false,
    type: "PAYABLE",
    item: null,
  });

  // Modal de Categoria
  const [isCategoryModalOpen, setIsCategoryModalOpen] = useState(false);
  const [newCatName, setNewCatName] = useState("");
  const [newCatType, setNewCatType] = useState<"RECEITA" | "DESPESA">("DESPESA");

  const fetchFinancialData = async () => {
    if (!activeCompany) return;
    setLoading(true);
    try {
      const [sumData, payData, recData, catData] = await Promise.all([
        financeService.getFinancialSummary(activeCompany.id),
        financeService.getPayables(activeCompany.id),
        financeService.getReceivables(activeCompany.id),
        financeService.getCategories(activeCompany.id),
      ]);
      setSummary(sumData);
      setPayables(payData);
      setReceivables(recData);
      setCategories(catData);
    } catch (err) {
      console.error("Erro ao carregar dados financeiros:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFinancialData();
  }, [activeCompany]);

  const handleCreateCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCatName.trim() || !activeCompany) return;
    try {
      await financeService.createCategory(
        { name: newCatName.trim(), type: newCatType },
        activeCompany.id
      );
      setNewCatName("");
      setIsCategoryModalOpen(false);
      fetchFinancialData();
    } catch (err: any) {
      alert(err?.message || "Erro ao criar categoria.");
    }
  };

  const filteredPayables = payables.filter((p) => {
    const matchesSearch =
      p.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (p.supplier_name && p.supplier_name.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesStatus = statusFilter === "ALL" || p.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const filteredReceivables = receivables.filter((r) => {
    const matchesSearch =
      r.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (r.customer_name && r.customer_name.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesStatus = statusFilter === "ALL" || r.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "PENDING":
        return (
          <Badge variant="outline" className="gap-1 border-amber-500/40 text-amber-500 bg-amber-500/10">
            <Clock className="h-3 w-3" /> Pendente
          </Badge>
        );
      case "PAID":
      case "RECEIVED":
        return (
          <Badge variant="success" className="gap-1">
            <CheckCircle2 className="h-3 w-3" /> {status === "PAID" ? "Pago" : "Recebido"}
          </Badge>
        );
      case "OVERDUE":
        return (
          <Badge variant="destructive" className="gap-1">
            <AlertTriangle className="h-3 w-3" /> Vencido
          </Badge>
        );
      case "CANCELED":
        return (
          <Badge variant="outline" className="gap-1 text-muted-foreground">
            <XCircle className="h-3 w-3" /> Cancelado
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight flex items-center gap-2">
            <DollarSign className="h-6 w-6 text-primary" /> Módulo Financeiro & Fluxo de Caixa
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Controle integrado de contas a pagar, contas a receber e liquidações
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            onClick={() => setIsPayableModalOpen(true)}
            className="gap-2 bg-rose-600 hover:bg-rose-700 text-white text-xs h-9 font-semibold"
          >
            <ArrowDownLeft className="h-4 w-4" /> + Conta a Pagar
          </Button>

          <Button
            onClick={() => setIsReceivableModalOpen(true)}
            className="gap-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs h-9 font-semibold"
          >
            <ArrowUpRight className="h-4 w-4" /> + Conta a Receber
          </Button>
        </div>
      </div>

      {/* Financial Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Receber Pendente */}
        <div className="p-4 bg-card border border-border rounded-xl shadow-sm space-y-1">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">A Receber Pendente</span>
            <ArrowUpRight className="h-4 w-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-extrabold font-mono text-foreground">
            R$ {summary.total_receivable_pending.toFixed(2)}
          </div>
        </div>

        {/* Pagar Pendente */}
        <div className="p-4 bg-card border border-border rounded-xl shadow-sm space-y-1">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-semibold text-rose-600 dark:text-rose-400">A Pagar Pendente</span>
            <ArrowDownLeft className="h-4 w-4 text-rose-500" />
          </div>
          <div className="text-2xl font-extrabold font-mono text-foreground">
            R$ {summary.total_payable_pending.toFixed(2)}
          </div>
        </div>

        {/* Total Vencido */}
        <div className="p-4 bg-card border border-border rounded-xl shadow-sm space-y-1">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-semibold text-amber-600 dark:text-amber-400">Total Vencido</span>
            <AlertTriangle className="h-4 w-4 text-amber-500" />
          </div>
          <div className="text-2xl font-extrabold font-mono text-amber-600 dark:text-amber-400">
            R$ {summary.total_overdue.toFixed(2)}
          </div>
        </div>

        {/* Projeção de Saldo */}
        <div className="p-4 bg-card border border-border rounded-xl shadow-sm space-y-1">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-semibold text-blue-600 dark:text-blue-400">Projeção de Saldo</span>
            <TrendingUp className="h-4 w-4 text-blue-500" />
          </div>
          <div
            className={`text-2xl font-extrabold font-mono ${
              summary.forecast_balance >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"
            }`}
          >
            R$ {summary.forecast_balance.toFixed(2)}
          </div>
        </div>
      </div>

      {/* Tabs & Filters */}
      <div className="p-4 bg-card border border-border rounded-xl shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 border-b border-border pb-3">
          {/* Sub-tabs */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setActiveTab("payables");
                setStatusFilter("ALL");
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                activeTab === "payables"
                  ? "bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20"
                  : "text-muted-foreground hover:bg-muted"
              }`}
            >
              Contas a Pagar ({payables.length})
            </button>

            <button
              onClick={() => {
                setActiveTab("receivables");
                setStatusFilter("ALL");
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                activeTab === "receivables"
                  ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20"
                  : "text-muted-foreground hover:bg-muted"
              }`}
            >
              Contas a Receber ({receivables.length})
            </button>

            <button
              onClick={() => setActiveTab("categories")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                activeTab === "categories"
                  ? "bg-primary/10 text-primary border border-primary/20"
                  : "text-muted-foreground hover:bg-muted"
              }`}
            >
              Categorias ({categories.length})
            </button>

            <button
              onClick={() => setActiveTab("caixa")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                activeTab === "caixa"
                  ? "bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20"
                  : "text-muted-foreground hover:bg-muted"
              }`}
            >
              <Wallet className="h-3.5 w-3.5" /> Operações de Caixa
            </button>
          </div>

          <Button variant="outline" size="sm" onClick={fetchFinancialData} disabled={loading} className="gap-1.5 text-xs h-9">
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Atualizar
          </Button>
        </div>

        {/* Filter Toolbar for Payables & Receivables */}
        {activeTab !== "categories" && activeTab !== "caixa" && (
          <div className="flex flex-col sm:flex-row items-center gap-3">
            <div className="relative flex-1 w-full">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar por descrição, fornecedor ou cliente..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9 h-9 text-xs"
              />
            </div>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-9 rounded-md border border-input bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary w-full sm:w-auto"
            >
              <option value="ALL">Todos os Status</option>
              <option value="PENDING">Pendentes</option>
              <option value="OVERDUE">Vencidos</option>
              <option value={activeTab === "payables" ? "PAID" : "RECEIVED"}>
                {activeTab === "payables" ? "Pagos" : "Recebidos"}
              </option>
            </select>
          </div>
        )}
      </div>

      {/* Main Content Area */}
      {activeTab === "caixa" ? (
        <CashView />
      ) : (
        <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
          {loading ? (
            <div className="p-12 text-center text-xs text-muted-foreground flex flex-col items-center justify-center space-y-2">
              <RefreshCw className="h-6 w-6 animate-spin text-primary" />
              <span>Carregando dados financeiros...</span>
            </div>
          ) : activeTab === "payables" ? (
          /* Table Contas a Pagar */
          filteredPayables.length === 0 ? (
            <div className="p-12 text-center text-xs text-muted-foreground">Nenhuma conta a pagar encontrada.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-muted/60 text-muted-foreground font-medium border-b border-border">
                  <tr>
                    <th className="p-3">Vencimento</th>
                    <th className="p-3">Descrição</th>
                    <th className="p-3">Fornecedor</th>
                    <th className="p-3">Categoria</th>
                    <th className="p-3 text-center">Status</th>
                    <th className="p-3 text-right">Valor Total (R$)</th>
                    <th className="p-3 text-right">Valor Pago (R$)</th>
                    <th className="p-3 text-center">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filteredPayables.map((p) => (
                    <tr key={p.id} className="hover:bg-muted/30 transition-colors">
                      <td className="p-3 font-mono font-medium">{new Date(p.due_date).toLocaleDateString("pt-BR")}</td>
                      <td className="p-3 font-semibold text-foreground">{p.description}</td>
                      <td className="p-3 text-muted-foreground">{p.supplier_name || "-"}</td>
                      <td className="p-3 text-muted-foreground">{p.category_name || "-"}</td>
                      <td className="p-3 text-center">{getStatusBadge(p.status)}</td>
                      <td className="p-3 text-right font-mono font-bold text-foreground">R$ {p.amount.toFixed(2)}</td>
                      <td className="p-3 text-right font-mono text-emerald-600 dark:text-emerald-400 font-semibold">
                        R$ {p.paid_amount.toFixed(2)}
                      </td>
                      <td className="p-3 text-center">
                        {p.status !== "PAID" && p.status !== "CANCELED" && (
                          <Button
                            size="sm"
                            onClick={() =>
                              setPayOffModalState({
                                isOpen: true,
                                type: "PAYABLE",
                                item: p,
                              })
                            }
                            className="h-7 text-xs px-2.5 gap-1 bg-rose-600 hover:bg-rose-700 text-white"
                          >
                            <DollarSign className="h-3.5 w-3.5" /> Baixar
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        ) : activeTab === "receivables" ? (
          /* Table Contas a Receber */
          filteredReceivables.length === 0 ? (
            <div className="p-12 text-center text-xs text-muted-foreground">Nenhuma conta a receber encontrada.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-muted/60 text-muted-foreground font-medium border-b border-border">
                  <tr>
                    <th className="p-3">Vencimento</th>
                    <th className="p-3">Descrição</th>
                    <th className="p-3">Cliente</th>
                    <th className="p-3">Categoria</th>
                    <th className="p-3 text-center">Status</th>
                    <th className="p-3 text-right">Valor Total (R$)</th>
                    <th className="p-3 text-right">Valor Recebido (R$)</th>
                    <th className="p-3 text-center">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filteredReceivables.map((r) => (
                    <tr key={r.id} className="hover:bg-muted/30 transition-colors">
                      <td className="p-3 font-mono font-medium">{new Date(r.due_date).toLocaleDateString("pt-BR")}</td>
                      <td className="p-3 font-semibold text-foreground">{r.description}</td>
                      <td className="p-3 text-muted-foreground">{r.customer_name || "-"}</td>
                      <td className="p-3 text-muted-foreground">{r.category_name || "-"}</td>
                      <td className="p-3 text-center">{getStatusBadge(r.status)}</td>
                      <td className="p-3 text-right font-mono font-bold text-foreground">R$ {r.amount.toFixed(2)}</td>
                      <td className="p-3 text-right font-mono text-emerald-600 dark:text-emerald-400 font-semibold">
                        R$ {r.received_amount.toFixed(2)}
                      </td>
                      <td className="p-3 text-center">
                        {r.status !== "RECEIVED" && r.status !== "CANCELED" && (
                          <Button
                            size="sm"
                            onClick={() =>
                              setPayOffModalState({
                                isOpen: true,
                                type: "RECEIVABLE",
                                item: r,
                              })
                            }
                            className="h-7 text-xs px-2.5 gap-1 bg-emerald-600 hover:bg-emerald-700 text-white"
                          >
                            <DollarSign className="h-3.5 w-3.5" /> Baixar
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        ) : (
          /* Table Categorias Financeiras */
          <div className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-foreground">Plano de Contas & Categorias</span>
              <Button size="sm" onClick={() => setIsCategoryModalOpen(true)} className="h-8 text-xs gap-1.5 bg-primary">
                <Plus className="h-3.5 w-3.5" /> Nova Categoria
              </Button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {categories.map((c) => (
                <div key={c.id} className="p-3 rounded-lg border border-border bg-card flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Tag className="h-4 w-4" style={{ color: c.color || "#64748b" }} />
                    <span className="text-xs font-semibold text-foreground">{c.name}</span>
                  </div>
                  <Badge variant={c.type === "RECEITA" ? "success" : "destructive"} className="text-[10px]">
                    {c.type}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      )}

      {/* Modais */}
      <PayableModal
        isOpen={isPayableModalOpen}
        onClose={() => setIsPayableModalOpen(false)}
        onSuccess={() => fetchFinancialData()}
      />

      <ReceivableModal
        isOpen={isReceivableModalOpen}
        onClose={() => setIsReceivableModalOpen(false)}
        onSuccess={() => fetchFinancialData()}
      />

      <PayOffModal
        isOpen={payOffModalState.isOpen}
        type={payOffModalState.type}
        item={payOffModalState.item}
        onClose={() => setPayOffModalState({ isOpen: false, type: "PAYABLE", item: null })}
        onSuccess={() => fetchFinancialData()}
      />

      {/* Modal Criar Categoria */}
      {isCategoryModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-sm p-6 space-y-4">
            <h3 className="text-sm font-bold text-foreground">Nova Categoria Financeira</h3>
            <form onSubmit={handleCreateCategory} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold block mb-1">Nome da Categoria *</label>
                <Input
                  placeholder="Ex: Aluguel, Fornecedores, Vendas Diretas..."
                  value={newCatName}
                  onChange={(e) => setNewCatName(e.target.value)}
                  className="h-9 text-xs"
                  required
                />
              </div>

              <div>
                <label className="font-semibold block mb-1">Tipo *</label>
                <select
                  value={newCatType}
                  onChange={(e) => setNewCatType(e.target.value as any)}
                  className="w-full h-9 rounded-md border border-input bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="DESPESA">DESPESA (Conta a Pagar)</option>
                  <option value="RECEITA">RECEITA (Conta a Receber)</option>
                </select>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setIsCategoryModalOpen(false)} className="h-8 text-xs">
                  Cancelar
                </Button>
                <Button type="submit" className="h-8 text-xs bg-primary">
                  Salvar
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
