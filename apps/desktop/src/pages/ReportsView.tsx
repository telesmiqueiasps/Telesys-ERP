import { useState, useEffect, useCallback } from "react";
import {
  BarChart3,
  TrendingUp,
  DollarSign,
  ShoppingBag,
  CreditCard,
  Printer,
  RefreshCw,
  Calendar,
  PieChart,
  FileSpreadsheet,
  Boxes,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useAuthStore } from "@/store/useAuthStore";
import { reportsService } from "@/services/reportsService";
import {
  SalesSummaryReport,
  TopProductItem,
  DREStatementReport,
  InventorySummaryReport,
} from "@/types/reports";

export function ReportsView() {
  const { activeCompany } = useAuthStore();
  const [activeTab, setActiveTab] = useState<"sales" | "abc" | "dre" | "inventory">("sales");

  const [startDate, setStartDate] = useState<string>(
    new Date(new Date().setDate(new Date().getDate() - 30)).toISOString().split("T")[0]
  );
  const [endDate, setEndDate] = useState<string>(
    new Date().toISOString().split("T")[0]
  );

  const [summary, setSummary] = useState<SalesSummaryReport | null>(null);
  const [topProducts, setTopProducts] = useState<TopProductItem[]>([]);
  const [dre, setDre] = useState<DREStatementReport | null>(null);
  const [inventory, setInventory] = useState<InventorySummaryReport | null>(null);
  const [inventoryFilter, setInventoryFilter] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const loadReports = useCallback(async () => {
    if (!activeCompany) return;
    setLoading(true);
    try {
      const [sumData, abcData, dreData, invData] = await Promise.all([
        reportsService.getSalesSummary(activeCompany.id, startDate, endDate),
        reportsService.getTopProducts(activeCompany.id, 20),
        reportsService.getDREStatement(activeCompany.id, startDate, endDate),
        reportsService.getInventoryReport(activeCompany.id, inventoryFilter),
      ]);
      setSummary(sumData);
      setTopProducts(abcData);
      setDre(dreData);
      setInventory(invData);
    } catch (err) {
      console.error("Erro ao carregar relatórios BI:", err);
    } finally {
      setLoading(false);
    }
  }, [activeCompany, startDate, endDate, inventoryFilter]);

  useEffect(() => {
    loadReports();
  }, [loadReports]);

  const handlePrintReport = () => {
    window.print();
  };

  const paymentLabels: Record<string, string> = {
    MONEY: "Dinheiro (Espécie)",
    PIX: "PIX Instantâneo",
    CREDIT_CARD: "Cartão de Crédito",
    DEBIT_CARD: "Cartão de Débito",
    STORE_CREDIT: "Crediário / Fiado",
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center font-bold">
              <BarChart3 className="h-5 w-5" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight">Relatórios BI, DRE & Inventário</h1>
          </div>
          <p className="text-sm text-slate-400">
            Inteligência de vendas, curva ABC, inventário de estoque e demonstração de resultados.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handlePrintReport}
            className="text-xs gap-1.5 border-slate-700 text-slate-300 hover:text-white"
          >
            <Printer className="h-3.5 w-3.5" /> Imprimir / Exportar PDF
          </Button>

          <Button
            size="sm"
            onClick={loadReports}
            disabled={loading}
            className="text-xs gap-1.5 bg-blue-600 hover:bg-blue-500 text-white"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} /> Atualizar
          </Button>
        </div>
      </div>

      {/* Filter Bar */}
      <Card className="p-4 bg-slate-900 border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
          <div className="flex items-center space-x-2 text-xs text-slate-400">
            <Calendar className="w-4 h-4 text-emerald-400" />
            <span>Período:</span>
          </div>

          <Input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-36 text-xs bg-slate-950 border-slate-800 text-white"
          />

          <span className="text-xs text-slate-500">até</span>

          <Input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-36 text-xs bg-slate-950 border-slate-800 text-white"
          />

          <Button
            size="sm"
            onClick={loadReports}
            className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200"
          >
            Filtrar
          </Button>
        </div>

        {/* Sub-tabs selector */}
        <div className="flex items-center p-1 bg-slate-950 rounded-lg border border-slate-800 w-full sm:w-auto overflow-x-auto">
          <button
            onClick={() => setActiveTab("sales")}
            className={`px-3 py-1.5 rounded text-xs font-semibold transition ${
              activeTab === "sales" ? "bg-emerald-600 text-white" : "text-slate-400 hover:text-white"
            }`}
          >
            Vendas & Horários
          </button>
          <button
            onClick={() => setActiveTab("abc")}
            className={`px-3 py-1.5 rounded text-xs font-semibold transition ${
              activeTab === "abc" ? "bg-emerald-600 text-white" : "text-slate-400 hover:text-white"
            }`}
          >
            Curva ABC
          </button>
          <button
            onClick={() => setActiveTab("inventory")}
            className={`px-3 py-1.5 rounded text-xs font-semibold transition ${
              activeTab === "inventory" ? "bg-emerald-600 text-white" : "text-slate-400 hover:text-white"
            }`}
          >
            Inventário & Estoque
          </button>
          <button
            onClick={() => setActiveTab("dre")}
            className={`px-3 py-1.5 rounded text-xs font-semibold transition ${
              activeTab === "dre" ? "bg-emerald-600 text-white" : "text-slate-400 hover:text-white"
            }`}
          >
            DRE Gerencial
          </button>
        </div>
      </Card>

      {/* Top Metrics Cards */}
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
              <span>Total Faturado</span>
              <DollarSign className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-extrabold text-emerald-400">
              R$ {summary.total_revenue.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
            </div>
            <div className="text-[11px] text-slate-500">Receita bruta do período</div>
          </Card>

          <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
              <span>Ticket Médio</span>
              <TrendingUp className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-2xl font-extrabold text-blue-400">
              R$ {summary.average_ticket.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
            </div>
            <div className="text-[11px] text-slate-500">Média gasto por cliente</div>
          </Card>

          <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
              <span>Vendas Realizadas</span>
              <ShoppingBag className="w-4 h-4 text-indigo-400" />
            </div>
            <div className="text-2xl font-extrabold text-white">{summary.total_sales_count}</div>
            <div className="text-[11px] text-slate-500">Cupons de venda finalizados</div>
          </Card>

          <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
              <span>Itens Vendidos</span>
              <PieChart className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-extrabold text-amber-400">{summary.total_items_sold}</div>
            <div className="text-[11px] text-slate-500">Unidades comercializadas</div>
          </Card>
        </div>
      )}

      {/* Tab 1: Sales & Hourly */}
      {activeTab === "sales" && summary && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Payment Methods */}
          <Card className="p-5 bg-slate-900 border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <CreditCard className="w-4 h-4 text-emerald-400" />
              <span>Vendas por Forma de Pagamento</span>
            </h3>

            <div className="space-y-3">
              {summary.payment_methods.map((pm) => {
                const pct = summary.total_revenue > 0 ? (pm.total_amount / summary.total_revenue) * 100 : 0;
                return (
                  <div key={pm.payment_method} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="font-semibold text-slate-300">
                        {paymentLabels[pm.payment_method] || pm.payment_method}
                      </span>
                      <span className="font-mono text-emerald-400 font-bold">
                        R$ {pm.total_amount.toLocaleString("pt-BR", { minimumFractionDigits: 2 })} ({pct.toFixed(1)}%)
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
              {summary.payment_methods.length === 0 && (
                <div className="py-6 text-center text-xs text-slate-500">Nenhuma venda no período.</div>
              )}
            </div>
          </Card>

          {/* Peak Hours Distribution */}
          <Card className="p-5 bg-slate-900 border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <BarChart3 className="w-4 h-4 text-blue-400" />
              <span>Horários de Pico do PDV (00h às 23h)</span>
            </h3>

            <div className="grid grid-cols-12 gap-1 items-end h-40 pt-4 border-b border-slate-800">
              {summary.hourly_distribution.map((h) => {
                const maxRev = Math.max(...summary.hourly_distribution.map((i) => i.total_revenue), 1);
                const heightPct = (h.total_revenue / maxRev) * 100;
                return (
                  <div key={h.hour} className="flex flex-col items-center group relative">
                    <div
                      className="w-full bg-blue-500/80 hover:bg-blue-400 rounded-t transition-all"
                      style={{ height: `${Math.max(heightPct, 4)}%` }}
                    />
                    <span className="text-[10px] text-slate-500 mt-1 font-mono">{h.hour}h</span>
                    <div className="absolute bottom-full mb-1 hidden group-hover:block bg-slate-800 text-white text-[10px] p-1.5 rounded shadow z-10 whitespace-nowrap">
                      {h.hour}h: R$ {h.total_revenue.toFixed(2)} ({h.sales_count} vendas)
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>
      )}

      {/* Tab 2: ABC Product Curve */}
      {activeTab === "abc" && (
        <Card className="bg-slate-900 border-slate-800 overflow-hidden">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-amber-400" />
              <span>Ranking Curva ABC (Produtos Mais Lucrativos)</span>
            </h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-800/60 text-slate-400 font-semibold uppercase border-b border-slate-800">
                <tr>
                  <th className="p-3">Posição</th>
                  <th className="p-3">Produto</th>
                  <th className="p-3">Qtd Vendida</th>
                  <th className="p-3">Faturamento Total</th>
                  <th className="p-3">Custo Unitário</th>
                  <th className="p-3">Margem Bruta (R$)</th>
                  <th className="p-3 text-right">Margem %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {topProducts.map((p, index) => (
                  <tr key={p.product_id} className="hover:bg-slate-800/30 transition">
                    <td className="p-3 font-bold text-slate-400">#{index + 1}</td>
                    <td className="p-3 font-semibold text-white">{p.product_name}</td>
                    <td className="p-3 font-mono">{p.quantity_sold} UN</td>
                    <td className="p-3 font-mono text-emerald-400 font-bold">
                      R$ {p.total_revenue.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                    </td>
                    <td className="p-3 font-mono text-slate-400">
                      R$ {p.cost_price.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                    </td>
                    <td className="p-3 font-mono text-indigo-400 font-bold">
                      R$ {p.profit_margin_amount.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                    </td>
                    <td className="p-3 text-right font-mono font-bold text-amber-400">
                      {p.profit_margin_percent}%
                    </td>
                  </tr>
                ))}
                {topProducts.length === 0 && (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-slate-500">
                      Nenhum produto vendido no período.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Tab 3: Inventory & Stock Valuation */}
      {activeTab === "inventory" && inventory && (
        <div className="space-y-4">
          {/* Inventory KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="p-4 bg-slate-900 border-slate-800 space-y-1">
              <div className="text-xs font-semibold text-slate-400 uppercase">Custo Total Investido</div>
              <div className="text-xl font-extrabold text-blue-400">
                R$ {inventory.total_cost_value.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </div>
              <div className="text-[11px] text-slate-500">{inventory.total_units} unidades em estoque</div>
            </Card>

            <Card className="p-4 bg-slate-900 border-slate-800 space-y-1">
              <div className="text-xs font-semibold text-slate-400 uppercase">Valor de Venda Total</div>
              <div className="text-xl font-extrabold text-emerald-400">
                R$ {inventory.total_selling_value.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </div>
              <div className="text-[11px] text-slate-500">Preço bruto praticado</div>
            </Card>

            <Card className="p-4 bg-slate-900 border-slate-800 space-y-1">
              <div className="text-xs font-semibold text-slate-400 uppercase">Lucro Bruto Projetado</div>
              <div className="text-xl font-extrabold text-amber-400">
                R$ {inventory.total_potential_profit.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </div>
              <div className="text-[11px] text-slate-500">Margem em caso de liquidação</div>
            </Card>

            <Card className="p-4 bg-slate-900 border-slate-800 space-y-1">
              <div className="text-xs font-semibold text-slate-400 uppercase">Alertas de Estoque</div>
              <div className="text-xl font-extrabold text-red-400">
                {inventory.low_stock_count + inventory.out_of_stock_count} produtos
              </div>
              <div className="text-[11px] text-slate-500">
                {inventory.low_stock_count} baixos | {inventory.out_of_stock_count} zerados
              </div>
            </Card>
          </div>

          {/* Inventory Table */}
          <Card className="bg-slate-900 border-slate-800 overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <Boxes className="w-4 h-4 text-emerald-400" />
                <span>Posição do Inventário de Produtos ({inventory.items.length})</span>
              </h3>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setInventoryFilter("")}
                  className={`px-2.5 py-1 text-xs rounded font-medium ${
                    inventoryFilter === "" ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-400 hover:text-white"
                  }`}
                >
                  Todos
                </button>
                <button
                  onClick={() => setInventoryFilter("LOW_STOCK")}
                  className={`px-2.5 py-1 text-xs rounded font-medium ${
                    inventoryFilter === "LOW_STOCK" ? "bg-amber-600 text-white" : "bg-slate-800 text-slate-400 hover:text-white"
                  }`}
                >
                  Estoque Baixo ({inventory.low_stock_count})
                </button>
                <button
                  onClick={() => setInventoryFilter("OUT_OF_STOCK")}
                  className={`px-2.5 py-1 text-xs rounded font-medium ${
                    inventoryFilter === "OUT_OF_STOCK" ? "bg-red-600 text-white" : "bg-slate-800 text-slate-400 hover:text-white"
                  }`}
                >
                  Zerados ({inventory.out_of_stock_count})
                </button>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-800/60 text-slate-400 font-semibold uppercase border-b border-slate-800">
                  <tr>
                    <th className="p-3">Produto / Código</th>
                    <th className="p-3">Categoria</th>
                    <th className="p-3">Estoque Atual</th>
                    <th className="p-3">Estoque Mín.</th>
                    <th className="p-3">Custo Unit.</th>
                    <th className="p-3">Preço Venda</th>
                    <th className="p-3">Custo Total</th>
                    <th className="p-3">Venda Total</th>
                    <th className="p-3 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {inventory.items.map((p) => (
                    <tr key={p.product_id} className="hover:bg-slate-800/30 transition">
                      <td className="p-3">
                        <div className="font-semibold text-white">{p.product_name}</div>
                        {p.barcode && <div className="text-[10px] text-slate-500 font-mono">{p.barcode}</div>}
                      </td>
                      <td className="p-3 text-slate-400">{p.category_name}</td>
                      <td className="p-3 font-mono font-bold text-white">
                        {p.current_stock} {p.unit_code}
                      </td>
                      <td className="p-3 font-mono text-slate-500">{p.min_stock} {p.unit_code}</td>
                      <td className="p-3 font-mono text-slate-400">R$ {p.cost_price.toFixed(2)}</td>
                      <td className="p-3 font-mono text-emerald-400">R$ {p.selling_price.toFixed(2)}</td>
                      <td className="p-3 font-mono text-blue-400 font-bold">R$ {p.total_cost_value.toFixed(2)}</td>
                      <td className="p-3 font-mono text-emerald-400 font-bold">R$ {p.total_selling_value.toFixed(2)}</td>
                      <td className="p-3 text-right">
                        {p.status_alert === "NORMAL" && (
                          <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                            OK
                          </span>
                        )}
                        {p.status_alert === "LOW_STOCK" && (
                          <span className="px-2 py-0.5 rounded text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
                            Baixo
                          </span>
                        )}
                        {p.status_alert === "OUT_OF_STOCK" && (
                          <span className="px-2 py-0.5 rounded text-[10px] bg-red-500/10 text-red-400 border border-red-500/20 font-medium">
                            Zerado
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}

                  {inventory.items.length === 0 && (
                    <tr>
                      <td colSpan={9} className="p-8 text-center text-slate-500">
                        Nenhum produto no inventário para este filtro.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* Tab 4: DRE Gerencial */}
      {activeTab === "dre" && dre && (
        <Card className="bg-slate-900 border-slate-800 p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <h3 className="text-base font-bold text-white flex items-center space-x-2">
                <FileSpreadsheet className="w-5 h-5 text-emerald-400" />
                <span>Demonstração do Resultado do Exercício (DRE Sintética)</span>
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Período analisado: {dre.period_start} até {dre.period_end}
              </p>
            </div>
            <Badge variant="outline" className="text-xs font-mono border-emerald-500/30 text-emerald-400">
              Lucro Líquido: {dre.net_profit_margin_percent}%
            </Badge>
          </div>

          <div className="space-y-3 font-mono text-xs max-w-2xl">
            <div className="flex justify-between py-2 border-b border-slate-800 text-slate-200">
              <span className="font-semibold text-white">(+) Receita Bruta de Vendas</span>
              <span className="font-bold text-emerald-400">
                R$ {dre.gross_revenue.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </span>
            </div>

            <div className="flex justify-between py-2 border-b border-slate-800/60 text-slate-400 pl-4">
              <span>(-) Descontos e Deduções</span>
              <span className="text-red-400">
                - R$ {dre.deductions.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </span>
            </div>

            <div className="flex justify-between py-2.5 bg-slate-850 px-3 rounded text-white font-bold">
              <span>(=) Receita Líquida de Vendas</span>
              <span className="text-emerald-400">
                R$ {dre.net_revenue.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </span>
            </div>

            <div className="flex justify-between py-2 border-b border-slate-800/60 text-slate-400 pl-4">
              <span>(-) Custo das Mercadorias Vendidas (CMV)</span>
              <span className="text-red-400">
                - R$ {dre.cost_of_goods_sold.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </span>
            </div>

            <div className="flex justify-between py-2.5 bg-slate-850 px-3 rounded text-white font-bold">
              <span>(=) Resultado Bruto (Margem Bruta {dre.gross_profit_margin_percent}%)</span>
              <span className="text-blue-400">
                R$ {dre.gross_profit.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </span>
            </div>

            <div className="flex justify-between py-2 border-b border-slate-800/60 text-slate-400 pl-4">
              <span>(-) Despesas Operacionais e Financeiras</span>
              <span className="text-red-400">
                - R$ {dre.operating_expenses.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </span>
            </div>

            <div
              className={`flex justify-between py-3 px-4 rounded-xl text-sm font-bold border ${
                dre.net_profit >= 0
                  ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                  : "bg-red-500/10 border-red-500/30 text-red-400"
              }`}
            >
              <span>(=) LUCRO / PREJUÍZO LÍQUIDO DO PERÍODO</span>
              <span className="text-base">
                R$ {dre.net_profit.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </span>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
