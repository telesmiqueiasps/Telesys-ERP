import { useState, useEffect } from "react";
import {
  Package,
  Plus,
  Search,
  Barcode,
  Tag,
  AlertTriangle,
  RefreshCw,
  CheckCircle2,
  DollarSign,
  Database,
  Edit,
  Trash2,
  SlidersHorizontal,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { apiFetch } from "@/lib/apiClient";
import { useAuthStore } from "@/store/useAuthStore";
import { ProductModal } from "@/components/ProductModal";
import { StockAdjustmentModal } from "@/components/StockAdjustmentModal";
import { localDbManager } from "@/services/localDb/databaseManager";
import { StockView } from "@/pages/StockView";

export interface ProductDetail {
  id: string;
  tenant_id: string;
  company_id: string;
  code?: string | null;
  name: string;
  description?: string | null;
  price: number;
  cost: number;
  stock_qty: number;
  min_stock_qty: number;
  is_active: boolean;
  ncm?: string | null;
  cest?: string | null;
  category?: { id: string; name: string } | null;
  unit?: { id: string; code: string; name: string } | null;
  barcodes?: Array<{ id: string; barcode: string }>;
  created_at: string;
}

export function ProductsView() {
  const { token, activeCompany } = useAuthStore();
  const [activeTab, setActiveTab] = useState<"catalog" | "stock">("catalog");
  const [products, setProducts] = useState<ProductDetail[]>([]);
  const [categories, setCategories] = useState<Array<{ id: string; name: string }>>([]);
  const [units, setUnits] = useState<Array<{ id: string; code: string; name: string }>>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [isProductModalOpen, setIsProductModalOpen] = useState(false);
  const [isStockModalOpen, setIsStockModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<ProductDetail | null>(null);
  const [syncStatus, setSyncStatus] = useState<string | null>(null);

  const fetchProducts = async () => {
    if (!token) return;
    setIsLoading(true);
    try {
      let endpoint = "/products";
      const params = new URLSearchParams();
      if (searchQuery) params.append("query", searchQuery);
      if (selectedCategory) params.append("category_id", selectedCategory);
      if (activeCompany) params.append("company_id", activeCompany.id);

      if (params.toString()) {
        endpoint += `?${params.toString()}`;
      }

      const data = await apiFetch<ProductDetail[]>(endpoint, {}, token);
      setProducts(data);
    } catch (err: any) {
      console.error("Erro ao buscar produtos:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAuxiliaryData = async () => {
    if (!token) return;
    try {
      const [catsData, unitsData] = await Promise.all([
        apiFetch<Array<{ id: string; name: string }>>("/products/categories", {}, token),
        apiFetch<Array<{ id: string; code: string; name: string }>>("/products/units", {}, token),
      ]);
      setCategories(catsData);
      setUnits(unitsData);
    } catch (err) {
      console.error("Erro ao carregar dados auxiliares de produtos:", err);
    }
  };

  useEffect(() => {
    fetchAuxiliaryData();
  }, [token]);

  useEffect(() => {
    fetchProducts();
  }, [token, searchQuery, selectedCategory, activeCompany]);

  const handleOpenCreateModal = () => {
    setEditingProduct(null);
    setIsProductModalOpen(true);
  };

  const handleOpenEditModal = (prod: ProductDetail) => {
    setEditingProduct(prod);
    setIsProductModalOpen(true);
  };

  const handleInactivateProduct = async (prod: ProductDetail) => {
    if (!token) return;
    if (confirm(`Deseja inativar o produto "${prod.name}"?`)) {
      try {
        await apiFetch(`/products/${prod.id}`, { method: "DELETE" }, token);
        fetchProducts();
      } catch (err: any) {
        alert(err.message || "Erro ao inativar produto");
      }
    }
  };

  const handleSyncLocalDb = async () => {
    if (!activeCompany) return;
    setSyncStatus("Sincronizando produtos no SQLite...");
    await localDbManager.openCompanyDatabase(activeCompany.id);
    setTimeout(() => {
      setSyncStatus(`✅ ${products.length} produtos sincronizados no SQLite da empresa!`);
      setTimeout(() => setSyncStatus(null), 4000);
    }, 600);
  };

  const totalStockValue = products.reduce((acc, p) => acc + (p.price * p.stock_qty), 0);
  const lowStockCount = products.filter((p) => p.stock_qty <= p.min_stock_qty).length;

  return (
    <div className="space-y-6">
      {/* Sub-Navigation Tabs */}
      <div className="flex items-center gap-2 border-b pb-3">
        <button
          onClick={() => setActiveTab("catalog")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-colors ${
            activeTab === "catalog"
              ? "bg-primary text-primary-foreground shadow-sm"
              : "bg-card border text-muted-foreground hover:bg-accent"
          }`}
        >
          <Package className="h-4 w-4" /> Catálogo de Produtos
        </button>

        <button
          onClick={() => setActiveTab("stock")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-colors ${
            activeTab === "stock"
              ? "bg-primary text-primary-foreground shadow-sm"
              : "bg-card border text-muted-foreground hover:bg-accent"
          }`}
        >
          <SlidersHorizontal className="h-4 w-4" /> Histórico & Movimentações de Estoque
        </button>
      </div>

      {activeTab === "stock" ? (
        <StockView />
      ) : (
        <>
          {/* Top Action Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
                <Package className="h-6 w-6 text-emerald-500" /> Catálogo de Produtos
              </h2>
              <p className="text-xs text-muted-foreground">
                Cadastre, edite e gerencie preços, custos e códigos de barras dos produtos
              </p>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleSyncLocalDb}
                className="gap-2 text-xs border-emerald-500/30 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/10"
              >
                <Database className="h-3.5 w-3.5" /> Sincronizar no SQLite
              </Button>

              <Button
                size="sm"
                onClick={handleOpenCreateModal}
                className="gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold"
              >
                <Plus className="h-4 w-4" /> Novo Produto
              </Button>
            </div>
          </div>

          {syncStatus && (
            <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs flex items-center gap-2 animate-in fade-in-50">
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              <span>{syncStatus}</span>
            </div>
          )}

          {/* Metrics Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card className="border-border/60">
              <CardHeader className="pb-2 space-y-0 flex flex-row items-center justify-between">
                <CardTitle className="text-xs text-muted-foreground font-semibold uppercase">Total de Produtos</CardTitle>
                <Package className="h-4 w-4 text-emerald-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{products.length}</div>
                <p className="text-xs text-muted-foreground mt-1">Itens no Catálogo</p>
              </CardContent>
            </Card>

            <Card className="border-border/60">
              <CardHeader className="pb-2 space-y-0 flex flex-row items-center justify-between">
                <CardTitle className="text-xs text-muted-foreground font-semibold uppercase">Valor do Estoque</CardTitle>
                <DollarSign className="h-4 w-4 text-blue-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  R$ {totalStockValue.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
                <p className="text-xs text-muted-foreground mt-1">Soma do Saldo × Preço Venda</p>
              </CardContent>
            </Card>

            <Card className="border-border/60">
              <CardHeader className="pb-2 space-y-0 flex flex-row items-center justify-between">
                <CardTitle className="text-xs text-muted-foreground font-semibold uppercase">Estoque Crítico</CardTitle>
                <AlertTriangle className="h-4 w-4 text-amber-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-amber-500">{lowStockCount}</div>
                <p className="text-xs text-muted-foreground mt-1">Abaixo do Saldo Mínimo</p>
              </CardContent>
            </Card>
          </div>

          {/* Filter and Search Toolbar */}
          <Card className="border-border/60">
            <CardContent className="p-4 flex flex-col sm:flex-row items-center gap-3">
              <div className="relative flex-1 w-full">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Buscar por Nome do Produto, SKU ou Código de Barras..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 text-xs"
                />
              </div>

              <div className="flex items-center gap-2 w-full sm:w-auto">
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="h-9 px-3 rounded-md border border-input bg-background text-xs focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="">Todas as Categorias</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>

                <Button variant="ghost" size="sm" onClick={fetchProducts} className="h-9 text-xs gap-1.5">
                  <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} /> Atualizar
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Data Table with Actions */}
          <Card className="border-border/60 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-muted/50 border-b text-muted-foreground font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4">Código / Barcode</th>
                    <th className="py-3 px-4">Produto</th>
                    <th className="py-3 px-4">Categoria</th>
                    <th className="py-3 px-4 text-right">Preço Custo</th>
                    <th className="py-3 px-4 text-right">Preço Venda</th>
                    <th className="py-3 px-4 text-right">Saldo Estoque</th>
                    <th className="py-3 px-4 text-center">Status</th>
                    <th className="py-3 px-4 text-center">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y border-b">
                  {products.length > 0 ? (
                    products.map((p) => {
                      const firstBarcode = p.barcodes && p.barcodes.length > 0 ? p.barcodes[0].barcode : null;
                      const isLowStock = p.stock_qty <= p.min_stock_qty;

                      return (
                        <tr key={p.id} className="hover:bg-muted/30 transition-colors">
                          <td className="py-3.5 px-4 font-mono">
                            <div className="space-y-0.5">
                              <span className="font-semibold text-foreground">{p.code || "N/A"}</span>
                              {firstBarcode && (
                                <div className="flex items-center gap-1 text-[11px] text-muted-foreground">
                                  <Barcode className="h-3 w-3 text-primary" /> {firstBarcode}
                                </div>
                              )}
                            </div>
                          </td>

                          <td className="py-3.5 px-4">
                            <span className="font-bold text-sm text-foreground">{p.name}</span>
                            {p.description && (
                              <p className="text-[11px] text-muted-foreground truncate max-w-xs">{p.description}</p>
                            )}
                          </td>

                          <td className="py-3.5 px-4">
                            {p.category ? (
                              <Badge variant="outline" className="text-[11px] font-normal">
                                <Tag className="h-3 w-3 mr-1 text-primary" /> {p.category.name}
                              </Badge>
                            ) : (
                              <span className="text-muted-foreground">-</span>
                            )}
                          </td>

                          <td className="py-3.5 px-4 text-right font-mono text-muted-foreground">
                            R$ {Number(p.cost).toFixed(2)}
                          </td>

                          <td className="py-3.5 px-4 text-right font-mono font-bold text-emerald-600 dark:text-emerald-400 text-sm">
                            R$ {Number(p.price).toFixed(2)}
                          </td>

                          <td className="py-3.5 px-4 text-right font-mono">
                            <span className={`font-bold ${isLowStock ? "text-amber-500" : "text-foreground"}`}>
                              {Number(p.stock_qty) % 1 === 0 ? Number(p.stock_qty).toLocaleString("pt-BR") : Number(p.stock_qty).toLocaleString("pt-BR", { minimumFractionDigits: 0, maximumFractionDigits: 3 })} {p.unit?.code || "UN"}
                            </span>
                            {isLowStock && (
                              <div className="text-[10px] text-amber-500 flex items-center justify-end gap-1">
                                <AlertTriangle className="h-3 w-3" /> Estoque baixo (mín: {Number(p.min_stock_qty) % 1 === 0 ? Number(p.min_stock_qty).toLocaleString("pt-BR") : Number(p.min_stock_qty).toLocaleString("pt-BR")})
                              </div>
                            )}
                          </td>

                          <td className="py-3.5 px-4 text-center">
                            <Badge variant={p.is_active ? "success" : "secondary"}>
                              {p.is_active ? "Ativo" : "Inativo"}
                            </Badge>
                          </td>

                          <td className="py-3.5 px-4 text-center">
                            <div className="flex items-center justify-center gap-1">
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-7 w-7 text-blue-500 hover:text-blue-600 hover:bg-blue-500/10"
                                onClick={() => handleOpenEditModal(p)}
                                title="Editar produto"
                              >
                                <Edit className="h-3.5 w-3.5" />
                              </Button>

                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-7 w-7 text-amber-500 hover:text-amber-600 hover:bg-amber-500/10"
                                onClick={() => setIsStockModalOpen(true)}
                                title="Ajustar estoque"
                              >
                                <SlidersHorizontal className="h-3.5 w-3.5" />
                              </Button>

                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-7 w-7 text-destructive hover:text-destructive hover:bg-destructive/10"
                                onClick={() => handleInactivateProduct(p)}
                                title="Inativar produto"
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan={8} className="py-12 text-center text-muted-foreground">
                        {isLoading ? (
                          <div className="flex justify-center items-center gap-2">
                            <RefreshCw className="h-4 w-4 animate-spin text-primary" /> Carregando produtos...
                          </div>
                        ) : (
                          "Nenhum produto cadastrado ou encontrado para os filtros selecionados."
                        )}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Product Registration / Edit Modal */}
          <ProductModal
            isOpen={isProductModalOpen}
            onClose={() => setIsProductModalOpen(false)}
            onSuccess={fetchProducts}
            categories={categories}
            units={units}
            productToEdit={editingProduct}
          />

          {/* Stock Adjustment Modal */}
          <StockAdjustmentModal
            isOpen={isStockModalOpen}
            onClose={() => setIsStockModalOpen(false)}
            onSuccess={fetchProducts}
            products={products}
          />
        </>
      )}
    </div>
  );
}
