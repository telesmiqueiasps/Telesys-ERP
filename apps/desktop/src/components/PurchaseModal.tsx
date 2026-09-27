import React, { useState, useEffect } from "react";
import { X, ShoppingBag, Plus, Trash2, Search, CheckCircle2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Supplier } from "@/types/customer";
import { Product } from "@/types/product";
import { PurchaseItemInput, PurchaseDetail } from "@/types/purchase";
import { purchaseService } from "@/services/purchaseService";
import { customerService } from "@/services/customerService";
import { productService } from "@/services/productService";
import { syncEngine } from "@/services/syncEngine";
import { useAuthStore } from "@/store/useAuthStore";

interface PurchaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (purchase: PurchaseDetail) => void;
}

export function PurchaseModal({ isOpen, onClose, onSuccess }: PurchaseModalProps) {
  const { activeCompany } = useAuthStore();
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [products, setProducts] = useState<Product[]>([]);

  const [selectedSupplierId, setSelectedSupplierId] = useState<string>("");
  const [items, setItems] = useState<PurchaseItemInput[]>([]);
  const [discountAmount, setDiscountAmount] = useState<string>("0.00");
  const [notes, setNotes] = useState<string>("");

  // Temp state for adding a product line
  const [productSearch, setProductSearch] = useState<string>("");
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [quantity, setQuantity] = useState<string>("1");
  const [unitCost, setUnitCost] = useState<string>("0.00");

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !activeCompany) return;

    const fetchData = async () => {
      try {
        const [suppList, prodList] = await Promise.all([
          customerService.getSuppliers(activeCompany.id),
          productService.getProducts(activeCompany.id),
        ]);
        setSuppliers(suppList);
        setProducts(prodList);
      } catch (err) {
        console.error("Erro ao carregar dados para modal de compra:", err);
      }
    };

    fetchData();
    // Reset form
    setSelectedSupplierId("");
    setItems([]);
    setDiscountAmount("0.00");
    setNotes("");
    setProductSearch("");
    setSelectedProduct(null);
    setQuantity("1");
    setUnitCost("0.00");
    setError(null);
  }, [isOpen, activeCompany]);

  if (!isOpen) return null;

  const handleSelectProduct = (prod: Product) => {
    setSelectedProduct(prod);
    setProductSearch(prod.name);
    setUnitCost(prod.cost_price.toFixed(2));
  };

  const handleAddItem = () => {
    if (!selectedProduct) {
      setError("Selecione um produto para adicionar à compra.");
      return;
    }
    const numQty = parseFloat(quantity);
    const numCost = parseFloat(unitCost);

    if (isNaN(numQty) || numQty <= 0) {
      setError("A quantidade deve ser um número maior que zero.");
      return;
    }
    if (isNaN(numCost) || numCost < 0) {
      setError("O custo unitário deve ser um número positivo.");
      return;
    }

    // Check if item already exists in items list
    const existingIndex = items.findIndex((i) => i.product_id === selectedProduct.id);
    if (existingIndex >= 0) {
      const updated = [...items];
      updated[existingIndex].quantity += numQty;
      updated[existingIndex].unit_cost = numCost;
      setItems(updated);
    } else {
      setItems([
        ...items,
        {
          product_id: selectedProduct.id,
          product_name: selectedProduct.name,
          quantity: numQty,
          unit_cost: numCost,
        },
      ]);
    }

    // Reset item input
    setSelectedProduct(null);
    setProductSearch("");
    setQuantity("1");
    setUnitCost("0.00");
    setError(null);
  };

  const handleRemoveItem = (index: number) => {
    setItems(items.filter((_, idx) => idx !== index));
  };

  const subtotal = items.reduce((acc, item) => acc + item.quantity * item.unit_cost, 0);
  const numDiscount = parseFloat(discountAmount) || 0;
  const totalAmount = Math.max(0, subtotal - numDiscount);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (items.length === 0) {
      setError("Adicione pelo menos um produto à compra.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const purchase = await purchaseService.createPurchase(
        {
          supplier_id: selectedSupplierId || null,
          items: items.map((i) => ({
            product_id: i.product_id,
            quantity: i.quantity,
            unit_cost: i.unit_cost,
          })),
          discount_amount: numDiscount,
          notes: notes.trim() || undefined,
        },
        activeCompany?.id
      );

      // Registrar evento no Sync Engine Local-First
      const user = useAuthStore.getState().user;
      if (user && activeCompany) {
        syncEngine.enqueueEvent({
          tenant_id: user.tenant_id,
          company_id: activeCompany.id,
          entity_type: "product",
          action: "UPDATE",
          payload: {
            purchase_id: purchase.id,
            purchase_code: purchase.code,
            total_amount: purchase.total_amount,
            items_count: purchase.items.length,
          },
        });
      }

      onSuccess(purchase);
      onClose();
    } catch (err: any) {
      console.error("Erro ao registrar entrada de compra:", err);
      setError(err?.message || "Falha ao registrar entrada de compra.");
    } finally {
      setLoading(false);
    }
  };

  const filteredProducts = products.filter((p) =>
    p.name.toLowerCase().includes(productSearch.toLowerCase()) ||
    (p.barcode && p.barcode.includes(productSearch)) ||
    (p.code && p.code.toLowerCase().includes(productSearch.toLowerCase()))
  );

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-4xl overflow-hidden animate-in fade-in zoom-in duration-200 flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-muted/40">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold">
              <ShoppingBag className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-foreground">Nova Entrada de Compra / Fornecedor</h2>
              <p className="text-xs text-muted-foreground">
                Lançamento de mercadorias com atualização automática de estoque e custos
              </p>
            </div>
          </div>
          <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-foreground" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 overflow-y-auto flex-1">
          {error && (
            <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-xs flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Supplier Selection */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-semibold text-foreground mb-1 block">Fornecedor (Opcional)</label>
              <select
                value={selectedSupplierId}
                onChange={(e) => setSelectedSupplierId(e.target.value)}
                className="w-full h-9 rounded-md border border-input bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="">Nenhum Fornecedor Selecionado (Entrada Avulsa)</option>
                {suppliers.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} {s.document ? `(${s.document})` : ""}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-foreground mb-1 block">Observação / Nº Nota Fiscal</label>
              <Input
                placeholder="Ex: NF-e 001.234 - Compra de Reposição..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="h-9 text-xs"
              />
            </div>
          </div>

          <hr className="border-border" />

          {/* Product Add Bar */}
          <div className="space-y-2 bg-muted/30 p-3.5 rounded-lg border border-border">
            <span className="text-xs font-bold text-foreground">Adicionar Produto à Compra</span>
            <div className="grid grid-cols-1 md:grid-cols-12 gap-2 items-end">
              {/* Product Autocomplete */}
              <div className="md:col-span-5 relative">
                <label className="text-[11px] font-medium text-muted-foreground block mb-0.5">Buscar Produto</label>
                <div className="relative">
                  <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
                  <Input
                    placeholder="Nome, Código ou Cód. Barras..."
                    value={productSearch}
                    onChange={(e) => {
                      setProductSearch(e.target.value);
                      setSelectedProduct(null);
                    }}
                    className="pl-8 h-9 text-xs"
                  />
                </div>

                {/* Dropdown Options */}
                {productSearch && !selectedProduct && filteredProducts.length > 0 && (
                  <div className="absolute top-full left-0 right-0 z-20 mt-1 bg-card border border-border rounded-md shadow-lg max-h-40 overflow-y-auto">
                    {filteredProducts.map((p) => (
                      <div
                        key={p.id}
                        onClick={() => handleSelectProduct(p)}
                        className="p-2 text-xs hover:bg-accent cursor-pointer flex items-center justify-between"
                      >
                        <span className="font-medium text-foreground">{p.name}</span>
                        <span className="text-[10px] text-muted-foreground font-mono">
                          Estoque: {p.stock_qty} | Custo: R$ {p.cost_price.toFixed(2)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Quantity */}
              <div className="md:col-span-2">
                <label className="text-[11px] font-medium text-muted-foreground block mb-0.5">Qtd Comprada</label>
                <Input
                  type="number"
                  step="0.001"
                  min="0.001"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  className="h-9 text-xs font-semibold"
                />
              </div>

              {/* Unit Cost */}
              <div className="md:col-span-3">
                <label className="text-[11px] font-medium text-muted-foreground block mb-0.5">Custo Unitário (R$)</label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  value={unitCost}
                  onChange={(e) => setUnitCost(e.target.value)}
                  className="h-9 text-xs font-semibold"
                />
              </div>

              {/* Add Button */}
              <div className="md:col-span-2">
                <Button type="button" onClick={handleAddItem} className="w-full h-9 text-xs gap-1.5 bg-primary hover:bg-primary/90">
                  <Plus className="h-3.5 w-3.5" /> Inserir
                </Button>
              </div>
            </div>
          </div>

          {/* Items Table */}
          <div className="border border-border rounded-lg max-h-[220px] overflow-y-auto">
            {items.length === 0 ? (
              <div className="p-6 text-center text-xs text-muted-foreground">
                Nenhum item adicionado nesta compra ainda. Use o campo acima para adicionar produtos.
              </div>
            ) : (
              <table className="w-full text-xs text-left">
                <thead className="bg-muted/60 text-muted-foreground sticky top-0 font-medium">
                  <tr>
                    <th className="p-2.5">Item</th>
                    <th className="p-2.5">Produto</th>
                    <th className="p-2.5 text-right">Qtd</th>
                    <th className="p-2.5 text-right">Custo Unit. (R$)</th>
                    <th className="p-2.5 text-right">Subtotal (R$)</th>
                    <th className="p-2.5 text-center">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {items.map((item, index) => (
                    <tr key={index} className="hover:bg-muted/30 transition-colors">
                      <td className="p-2.5 font-mono text-muted-foreground">{index + 1}</td>
                      <td className="p-2.5 font-semibold text-foreground">{item.product_name}</td>
                      <td className="p-2.5 text-right font-mono">{item.quantity}</td>
                      <td className="p-2.5 text-right font-mono">R$ {item.unit_cost.toFixed(2)}</td>
                      <td className="p-2.5 text-right font-mono font-bold text-emerald-600 dark:text-emerald-400">
                        R$ {(item.quantity * item.unit_cost).toFixed(2)}
                      </td>
                      <td className="p-2.5 text-center">
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-destructive hover:text-destructive hover:bg-destructive/10"
                          onClick={() => handleRemoveItem(index)}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* Financial Summary */}
          <div className="p-4 bg-muted/40 border border-border rounded-lg flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4 text-xs">
              <div>
                <span className="text-muted-foreground block">Subtotal dos Itens:</span>
                <span className="text-sm font-bold font-mono">R$ {subtotal.toFixed(2)}</span>
              </div>
              <div>
                <span className="text-muted-foreground block">Desconto (R$):</span>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  value={discountAmount}
                  onChange={(e) => setDiscountAmount(e.target.value)}
                  className="h-8 w-28 text-xs font-mono"
                />
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-right">
                <span className="text-xs text-muted-foreground block">Total da Entrada:</span>
                <span className="text-xl font-extrabold font-mono text-emerald-600 dark:text-emerald-400">
                  R$ {totalAmount.toFixed(2)}
                </span>
              </div>

              <div className="flex items-center gap-2">
                <Button type="button" variant="outline" onClick={onClose} className="h-9 text-xs">
                  Cancelar
                </Button>
                <Button
                  type="submit"
                  disabled={loading || items.length === 0}
                  className="h-9 text-xs gap-1.5 bg-primary hover:bg-primary/90"
                >
                  <CheckCircle2 className="h-4 w-4" />
                  {loading ? "Registrando..." : "Finalizar Entrada"}
                </Button>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
