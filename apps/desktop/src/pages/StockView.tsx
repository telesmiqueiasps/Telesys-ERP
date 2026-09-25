import { useState, useEffect } from "react";
import {
  Package,
  Plus,
  ArrowUpRight,
  ArrowDownLeft,
  RefreshCw,
  Clock,
  UserCheck,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiFetch } from "@/lib/apiClient";
import { useAuthStore } from "@/store/useAuthStore";
import { StockAdjustmentModal } from "@/components/StockAdjustmentModal";
import { ProductDetail } from "@/pages/ProductsView";

export interface StockMovementRecord {
  id: string;
  tenant_id: string;
  company_id: string;
  product_id: string;
  user_id: string;
  movement_type: string;
  quantity: number;
  previous_qty: number;
  new_qty: number;
  unit_cost?: number | null;
  reference_doc?: string | null;
  notes?: string | null;
  created_at: string;
  product?: { name: string; code?: string | null; unit?: { code: string } | null } | null;
  user?: { name: string } | null;
}

export function StockView() {
  const { token, activeCompany } = useAuthStore();
  const [movements, setMovements] = useState<StockMovementRecord[]>([]);
  const [products, setProducts] = useState<ProductDetail[]>([]);
  const [selectedType, setSelectedType] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchMovements = async () => {
    if (!token) return;
    setIsLoading(true);
    try {
      let endpoint = "/stock/movements";
      const params = new URLSearchParams();
      if (activeCompany) params.append("company_id", activeCompany.id);
      if (selectedType) params.append("movement_type", selectedType);

      if (params.toString()) {
        endpoint += `?${params.toString()}`;
      }

      const data = await apiFetch<StockMovementRecord[]>(endpoint, {}, token);
      setMovements(data);
    } catch (err) {
      console.error("Erro ao buscar histórico de estoque:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchProductsList = async () => {
    if (!token) return;
    try {
      const endpoint = activeCompany ? `/products?company_id=${activeCompany.id}` : "/products";
      const data = await apiFetch<ProductDetail[]>(endpoint, {}, token);
      setProducts(data);
    } catch (err) {
      console.error("Erro ao buscar lista de produtos para o estoque:", err);
    }
  };

  useEffect(() => {
    fetchProductsList();
  }, [token, activeCompany]);

  useEffect(() => {
    fetchMovements();
  }, [token, selectedType, activeCompany]);

  const formatQuantity = (val: number) => {
    const num = Number(val) || 0;
    if (num % 1 === 0) {
      return num.toLocaleString("pt-BR");
    }
    return num.toLocaleString("pt-BR", { minimumFractionDigits: 0, maximumFractionDigits: 3 });
  };

  const totalEntries = movements.filter((m) => m.quantity > 0).length;
  const totalExits = movements.filter((m) => m.quantity < 0).length;

  return (
    <div className="space-y-6">
      {/* Top Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Package className="h-6 w-6 text-blue-500" /> Histórico & Ajustes de Estoque
          </h2>
          <p className="text-xs text-muted-foreground">
            Trilha de auditoria imutável (Append-Only) com saldo anterior, novo saldo e responsável
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={fetchMovements} className="h-9 text-xs gap-1.5">
            <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} /> Atualizar
          </Button>

          <Button
            size="sm"
            onClick={() => setIsModalOpen(true)}
            className="gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold"
          >
            <Plus className="h-4 w-4" /> Nova Movimentação / Ajuste
          </Button>
        </div>
      </div>

      {/* Metrics Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="border-border/60">
          <CardHeader className="pb-2 space-y-0 flex flex-row items-center justify-between">
            <CardTitle className="text-xs text-muted-foreground font-semibold uppercase">Total de Registros</CardTitle>
            <Clock className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{movements.length}</div>
            <p className="text-xs text-muted-foreground mt-1">Movimentações Auditadas</p>
          </CardContent>
        </Card>

        <Card className="border-border/60">
          <CardHeader className="pb-2 space-y-0 flex flex-row items-center justify-between">
            <CardTitle className="text-xs text-muted-foreground font-semibold uppercase">Entradas de Estoque</CardTitle>
            <ArrowUpRight className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{totalEntries}</div>
            <p className="text-xs text-muted-foreground mt-1">Compras e Ajustes Positivos</p>
          </CardContent>
        </Card>

        <Card className="border-border/60">
          <CardHeader className="pb-2 space-y-0 flex flex-row items-center justify-between">
            <CardTitle className="text-xs text-muted-foreground font-semibold uppercase">Saídas de Estoque</CardTitle>
            <ArrowDownLeft className="h-4 w-4 text-rose-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-rose-600 dark:text-rose-400">{totalExits}</div>
            <p className="text-xs text-muted-foreground mt-1">Vendas e Ajustes Negativos</p>
          </CardContent>
        </Card>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {[
          { id: "", label: "Todas as Movimentações" },
          { id: "ENTRADA_NF", label: "Entradas NF" },
          { id: "AJUSTE_ENTRADA", label: "Ajustes Entrada" },
          { id: "SAIDA_VENDA", label: "Saídas Venda" },
          { id: "AJUSTE_SAIDA", label: "Ajustes Saída" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setSelectedType(tab.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors ${
              selectedType === tab.id
                ? "bg-primary text-primary-foreground shadow-sm"
                : "bg-card border text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Data Table */}
      <Card className="border-border/60 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-muted/50 border-b text-muted-foreground font-semibold uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Data / Hora</th>
                <th className="py-3 px-4">Produto</th>
                <th className="py-3 px-4">Tipo Movimentação</th>
                <th className="py-3 px-4 text-right">Qtd. Movimentada</th>
                <th className="py-3 px-4 text-right">Saldo Anterior &rarr; Novo</th>
                <th className="py-3 px-4">Responsável</th>
                <th className="py-3 px-4">Documento / Obs</th>
              </tr>
            </thead>
            <tbody className="divide-y border-b">
              {movements.length > 0 ? (
                movements.map((m) => {
                  const dateStr = new Date(m.created_at).toLocaleString("pt-BR", {
                    day: "2-digit",
                    month: "2-digit",
                    year: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  });

                  const isPositive = m.quantity > 0;

                  return (
                    <tr key={m.id} className="hover:bg-muted/30 transition-colors">
                      <td className="py-3.5 px-4 font-mono text-muted-foreground whitespace-nowrap">
                        {dateStr}
                      </td>

                      <td className="py-3.5 px-4">
                        <span className="font-bold text-sm text-foreground">
                          {m.product?.name || "Produto"}
                        </span>
                        {m.product?.code && (
                          <span className="text-[11px] text-muted-foreground block font-mono">
                            SKU: {m.product.code}
                          </span>
                        )}
                      </td>

                      <td className="py-3.5 px-4">
                        <Badge
                          variant={isPositive ? "success" : "destructive"}
                          className="font-mono text-[10px]"
                        >
                          {m.movement_type}
                        </Badge>
                      </td>

                      <td className="py-3.5 px-4 text-right font-mono font-bold">
                        <span className={isPositive ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"}>
                          {isPositive ? "+" : ""}{formatQuantity(m.quantity)}
                        </span>
                      </td>

                      <td className="py-3.5 px-4 text-right font-mono text-muted-foreground">
                        {formatQuantity(m.previous_qty)} &rarr;{" "}
                        <strong className="text-foreground">{formatQuantity(m.new_qty)}</strong>
                      </td>

                      <td className="py-3.5 px-4 font-medium text-foreground">
                        <div className="flex items-center gap-1.5">
                          <UserCheck className="h-3.5 w-3.5 text-primary" />
                          <span>{m.user?.name || "Usuário"}</span>
                        </div>
                      </td>

                      <td className="py-3.5 px-4 text-muted-foreground max-w-xs truncate">
                        {m.reference_doc && (
                          <span className="font-semibold text-foreground mr-1.5 font-mono text-[11px]">
                            [{m.reference_doc}]
                          </span>
                        )}
                        {m.notes || "-"}
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-muted-foreground">
                    {isLoading ? (
                      <div className="flex justify-center items-center gap-2">
                        <RefreshCw className="h-4 w-4 animate-spin text-primary" /> Carregando movimentações...
                      </div>
                    ) : (
                      "Nenhuma movimentação de estoque registrada para este filtro."
                    )}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Stock Adjustment Modal */}
      <StockAdjustmentModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={fetchMovements}
        products={products}
      />
    </div>
  );
}
