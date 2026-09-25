import { useState, useEffect, useRef, useCallback } from "react";
import {
  ShoppingCart,
  Plus,
  Minus,
  Trash2,
  User,
  CreditCard,
  Keyboard,
  Barcode,
  Lock,
  RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CartItem, SaleDetail } from "@/types/sale";
import { Customer } from "@/types/customer";
import { ProductDetail } from "@/pages/ProductsView";
import { apiFetch } from "@/lib/apiClient";
import { useAuthStore } from "@/store/useAuthStore";
import { cashService } from "@/services/cashService";
import { customerService } from "@/services/customerService";
import { PaymentModal } from "@/components/PaymentModal";
import { ReceiptModal } from "@/components/ReceiptModal";
import { HotkeyHelpModal } from "@/components/HotkeyHelpModal";

export function PdvView() {
  const { activeCompany, token } = useAuthStore();

  // Cart & Search State
  const [cart, setCart] = useState<CartItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [products, setProducts] = useState<ProductDetail[]>([]);
  const [filteredProducts, setFilteredProducts] = useState<ProductDetail[]>([]);
  const [selectedCartIndex, setSelectedCartIndex] = useState<number>(0);

  // Customer State
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);

  // Cash Register Status State
  const [isCashOpen, setIsCashOpen] = useState<boolean>(true);

  // Modals
  const [isPaymentModalOpen, setIsPaymentModalOpen] = useState(false);
  const [isReceiptModalOpen, setIsReceiptModalOpen] = useState(false);
  const [isHotkeyHelpOpen, setIsHotkeyHelpOpen] = useState(false);
  const [completedSale, setCompletedSale] = useState<SaleDetail | null>(null);

  const searchInputRef = useRef<HTMLInputElement>(null);

  // Fetch Product Catalog & Cash status
  const loadInitialData = useCallback(async () => {
    if (!activeCompany) return;
    try {
      const [prodData, custData, cashData] = await Promise.all([
        apiFetch<ProductDetail[]>(`/products/?company_id=${activeCompany.id}`, { method: "GET" }, token),
        customerService.getCustomers(activeCompany.id, undefined, true),
        cashService.getCurrentCash(activeCompany.id),
      ]);
      setProducts(prodData);
      setCustomers(custData);
      setIsCashOpen(!!cashData);
    } catch (err) {
      console.error("Erro ao carregar dados do PDV:", err);
    }
  }, [activeCompany, token]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Focus search input on mount
  useEffect(() => {
    if (searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, []);

  // Filter products as search query changes
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredProducts([]);
      return;
    }
    const q = searchQuery.toLowerCase().trim();
    const matches = products.filter(
      (p) =>
        p.is_active &&
        (p.name.toLowerCase().includes(q) ||
          (p.code && p.code.toLowerCase().includes(q)) ||
          (p.barcodes && p.barcodes.some((b) => b.barcode.toLowerCase().includes(q))))
    );
    setFilteredProducts(matches);
  }, [searchQuery, products]);

  // Add Product to Cart
  const handleAddToCart = (product: ProductDetail) => {
    setCart((prevCart) => {
      const existingIdx = prevCart.findIndex((item) => item.id === product.id);
      if (existingIdx >= 0) {
        const updated = [...prevCart];
        const item = updated[existingIdx];
        const newQty = item.quantity + 1;
        updated[existingIdx] = {
          ...item,
          quantity: newQty,
          total_price: newQty * item.unit_price - item.discount_amount,
        };
        return updated;
      } else {
        const newItem: CartItem = {
          id: product.id,
          code: product.code,
          name: product.name,
          unit_code: product.unit?.code || "UN",
          unit_price: Number(product.price),
          quantity: 1,
          discount_amount: 0,
          total_price: Number(product.price),
          ncm: product.ncm,
          cest: product.cest,
        };
        return [...prevCart, newItem];
      }
    });
    setSearchQuery("");
    setFilteredProducts([]);
    if (searchInputRef.current) searchInputRef.current.focus();
  };

  // Handle Search Input Keydown (e.g. Enter on barcode scan)
  const handleSearchKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && searchQuery.trim()) {
      e.preventDefault();
      // Try exact barcode or code match first
      const exactMatch = products.find(
        (p) =>
          p.is_active &&
          ((p.code && p.code.toLowerCase() === searchQuery.toLowerCase().trim()) ||
            (p.barcodes && p.barcodes.some((b) => b.barcode === searchQuery.trim())))
      );

      if (exactMatch) {
        handleAddToCart(exactMatch);
      } else if (filteredProducts.length > 0) {
        handleAddToCart(filteredProducts[0]);
      }
    }
  };

  // Update Item Quantity
  const handleUpdateQuantity = (index: number, delta: number) => {
    setCart((prev) => {
      const updated = [...prev];
      const item = updated[index];
      const newQty = item.quantity + delta;
      if (newQty <= 0) {
        return updated.filter((_, i) => i !== index);
      }
      updated[index] = {
        ...item,
        quantity: newQty,
        total_price: newQty * item.unit_price - item.discount_amount,
      };
      return updated;
    });
  };

  // Remove Item
  const handleRemoveItem = (index: number) => {
    setCart((prev) => prev.filter((_, i) => i !== index));
  };

  // Clear Cart (New Sale - F2)
  const handleNewSale = () => {
    setCart([]);
    setSelectedCustomer(null);
    setSearchQuery("");
    if (searchInputRef.current) searchInputRef.current.focus();
  };

  // Hotkey Listener (F1 - F10, Esc)
  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if (isPaymentModalOpen || isReceiptModalOpen || isHotkeyHelpOpen) {
        if (e.key === "Escape") {
          setIsPaymentModalOpen(false);
          setIsReceiptModalOpen(false);
          setIsHotkeyHelpOpen(false);
        }
        return;
      }

      switch (e.key) {
        case "F1":
          e.preventDefault();
          setIsHotkeyHelpOpen(true);
          break;
        case "F2":
          e.preventDefault();
          handleNewSale();
          break;
        case "F3":
          e.preventDefault();
          if (searchInputRef.current) searchInputRef.current.focus();
          break;
        case "F9":
          e.preventDefault();
          if (cart.length > 0 && selectedCartIndex >= 0 && selectedCartIndex < cart.length) {
            handleRemoveItem(selectedCartIndex);
          }
          break;
        case "F10":
          e.preventDefault();
          if (cart.length > 0 && isCashOpen) {
            setIsPaymentModalOpen(true);
          }
          break;
      }
    };

    window.addEventListener("keydown", handleGlobalKeyDown);
    return () => window.removeEventListener("keydown", handleGlobalKeyDown);
  }, [cart, selectedCartIndex, isCashOpen, isPaymentModalOpen, isReceiptModalOpen, isHotkeyHelpOpen]);

  // Cart Totals
  const cartSubtotal = cart.reduce((acc, item) => acc + item.total_price, 0);
  const cartTotalItems = cart.reduce((acc, item) => acc + item.quantity, 0);

  return (
    <div className="space-y-4 max-w-7xl mx-auto">
      {/* Top PDV Banner & Cash Warning */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-card p-4 rounded-xl border border-border/60 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold">
            <ShoppingCart className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight">PDV — Frente de Caixa</h1>
            <p className="text-xs text-muted-foreground">
              Vendas ultrarrápidas local-first com leitor de código de barras e atalhos de teclado.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {isCashOpen ? (
            <Badge variant="success" className="gap-1.5 px-3 py-1 text-xs font-semibold">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" /> Caixa Aberto
            </Badge>
          ) : (
            <Badge variant="destructive" className="gap-1.5 px-3 py-1 text-xs font-semibold">
              <Lock className="h-3.5 w-3.5" /> Caixa Fechado
            </Badge>
          )}

          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsHotkeyHelpOpen(true)}
            className="gap-1.5 text-xs font-semibold"
          >
            <Keyboard className="h-3.5 w-3.5 text-primary" /> F1 Ajuda
          </Button>
        </div>
      </div>

      {!isCashOpen && (
        <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl text-amber-600 dark:text-amber-400 flex items-center justify-between text-xs font-medium">
          <span>
            ⚠️ O caixa está fechado no momento. Abra o caixa na tela de <b>Financeiro & Caixa</b> antes de iniciar as vendas.
          </span>
          <Button variant="outline" size="sm" onClick={loadInitialData} className="gap-1.5 text-xs">
            <RefreshCw className="h-3 w-3" /> Verificar Novamente
          </Button>
        </div>
      )}

      {/* Main Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left Column (8 cols): Product Search & Cart Table */}
        <div className="lg:col-span-8 space-y-4">
          {/* Search Input Box */}
          <Card className="p-4 border-border/60 shadow-sm relative">
            <div className="relative">
              <Barcode className="absolute left-3.5 top-3 h-5 w-5 text-muted-foreground" />
              <Input
                ref={searchInputRef}
                placeholder="Escaneie o Código de Barras ou digite o nome do produto (Pressione F3 ou Enter)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={handleSearchKeyDown}
                className="pl-11 h-11 text-sm font-semibold shadow-inner"
                autoFocus
              />
            </div>

            {/* Dropdown Results list if typing name */}
            {filteredProducts.length > 0 && (
              <div className="absolute left-0 right-0 top-full mt-1 z-30 bg-card border border-border rounded-xl shadow-xl max-h-60 overflow-y-auto divide-y divide-border/60">
                {filteredProducts.map((prod) => (
                  <button
                    key={prod.id}
                    onClick={() => handleAddToCart(prod)}
                    className="w-full text-left p-3 hover:bg-muted/40 transition-colors flex items-center justify-between"
                  >
                    <div>
                      <div className="font-semibold text-sm">{prod.name}</div>
                      <div className="text-xs text-muted-foreground font-mono">
                        SKU: {prod.code || "Sem código"} | Est: {Number(prod.stock_qty)} {prod.unit?.code || "UN"}
                      </div>
                    </div>
                    <div className="font-bold text-emerald-500 font-mono text-sm">
                      R$ {Number(prod.price).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </Card>

          {/* Cart Table */}
          <Card className="border-border/60 overflow-hidden shadow-sm flex flex-col min-h-[380px]">
            <div className="p-3 bg-muted/40 border-b border-border flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                <ShoppingCart className="h-4 w-4 text-primary" /> Carrinho de Compras ({cart.length} itens)
              </span>
              {cart.length > 0 && (
                <Button variant="ghost" size="sm" onClick={handleNewSale} className="h-7 text-xs text-destructive hover:bg-destructive/10">
                  <Trash2 className="h-3.5 w-3.5 mr-1" /> Limpar Carrinho (F2)
                </Button>
              )}
            </div>

            {cart.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center p-12 text-center text-muted-foreground space-y-3">
                <ShoppingCart className="h-12 w-12 text-muted-foreground/30" />
                <p className="text-sm font-semibold">Carrinho Vazio</p>
                <p className="text-xs max-w-xs text-muted-foreground">
                  Passe um produto pelo leitor de código de barras ou use a barra de busca acima para incluir itens na venda.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto flex-1">
                <table className="w-full text-left text-sm">
                  <thead className="bg-muted/20 border-b border-border/60 text-xs font-semibold text-muted-foreground uppercase">
                    <tr>
                      <th className="py-2.5 px-3">#</th>
                      <th className="py-2.5 px-3">Produto</th>
                      <th className="py-2.5 px-3 text-center">Qtd</th>
                      <th className="py-2.5 px-3 text-right">Preço Unit.</th>
                      <th className="py-2.5 px-3 text-right">Subtotal</th>
                      <th className="py-2.5 px-3 text-right">Ação</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/60">
                    {cart.map((item, idx) => (
                      <tr
                        key={item.id}
                        onClick={() => setSelectedCartIndex(idx)}
                        className={`cursor-pointer transition-colors ${
                          selectedCartIndex === idx
                            ? "bg-primary/10 font-semibold"
                            : "hover:bg-muted/30"
                        }`}
                      >
                        <td className="py-2.5 px-3 text-xs font-mono font-bold text-muted-foreground">
                          {(idx + 1).toString().padStart(2, "0")}
                        </td>
                        <td className="py-2.5 px-3">
                          <div className="font-semibold text-foreground text-xs">{item.name}</div>
                          {item.code && <div className="text-[10px] text-muted-foreground font-mono">{item.code}</div>}
                        </td>
                        <td className="py-2.5 px-3">
                          <div className="flex items-center justify-center gap-1">
                            <Button
                              variant="outline"
                              size="icon"
                              className="h-6 w-6 rounded"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleUpdateQuantity(idx, -1);
                              }}
                            >
                              <Minus className="h-3 w-3" />
                            </Button>
                            <span className="font-mono text-xs px-2 font-bold">{item.quantity}</span>
                            <Button
                              variant="outline"
                              size="icon"
                              className="h-6 w-6 rounded"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleUpdateQuantity(idx, 1);
                              }}
                            >
                              <Plus className="h-3 w-3" />
                            </Button>
                          </div>
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono text-xs">
                          R$ {item.unit_price.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono text-xs font-bold text-emerald-500">
                          R$ {item.total_price.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7 text-muted-foreground hover:text-destructive"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRemoveItem(idx);
                            }}
                            title="Remover Item (F9)"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>

        {/* Right Column (4 cols): Total Big Display, Customer & Checkout Actions */}
        <div className="lg:col-span-4 space-y-4">
          {/* Big Total Card */}
          <Card className="p-6 border-border/60 shadow-sm bg-card text-center space-y-2 relative overflow-hidden">
            <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
              Total Geral a Pagar
            </span>
            <div className="text-4xl font-extrabold tracking-tight font-mono text-emerald-500 my-1">
              R${" "}
              {cartSubtotal.toLocaleString("pt-BR", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </div>
            <div className="text-xs text-muted-foreground font-medium">
              {cartTotalItems} {cartTotalItems === 1 ? "item" : "itens"} no carrinho
            </div>
          </Card>

          {/* Customer Selection Card */}
          <Card className="p-4 border-border/60 shadow-sm space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                <User className="h-3.5 w-3.5 text-primary" /> Cliente na Venda (F4)
              </span>
              {selectedCustomer && (
                <button
                  onClick={() => setSelectedCustomer(null)}
                  className="text-[11px] text-destructive hover:underline font-semibold"
                >
                  Remover
                </button>
              )}
            </div>

            {selectedCustomer ? (
              <div className="p-2.5 bg-primary/10 border border-primary/20 rounded-lg text-xs space-y-0.5">
                <div className="font-bold text-foreground">{selectedCustomer.name}</div>
                {selectedCustomer.document && (
                  <div className="text-[10px] text-muted-foreground font-mono">
                    CPF/CNPJ: {selectedCustomer.document}
                  </div>
                )}
              </div>
            ) : (
              <select
                onChange={(e) => {
                  const cust = customers.find((c) => c.id === e.target.value);
                  setSelectedCustomer(cust || null);
                }}
                className="w-full h-9 px-3 rounded-lg border border-input bg-background text-xs font-medium focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="">Consumidor Final (Não identificado)</option>
                {customers.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} {c.document ? `(${c.document})` : ""}
                  </option>
                ))}
              </select>
            )}
          </Card>

          {/* Checkout Big Buttons */}
          <div className="space-y-2.5">
            <Button
              onClick={() => setIsPaymentModalOpen(true)}
              disabled={cart.length === 0 || !isCashOpen}
              className="w-full h-14 bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold text-base shadow-md gap-2 rounded-xl"
            >
              <CreditCard className="h-5 w-5" /> F10 - FINALIZAR VENDA
            </Button>

            <div className="grid grid-cols-2 gap-2">
              <Button
                variant="outline"
                onClick={handleNewSale}
                className="h-10 text-xs font-semibold gap-1.5"
              >
                F2 - NOVA VENDA
              </Button>
              <Button
                variant="outline"
                onClick={() => setIsHotkeyHelpOpen(true)}
                className="h-10 text-xs font-semibold gap-1.5"
              >
                F1 - ATALHOS
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Modals */}
      <PaymentModal
        isOpen={isPaymentModalOpen}
        subtotal={cartSubtotal}
        cartItems={cart}
        customer={selectedCustomer}
        onClose={() => setIsPaymentModalOpen(false)}
        onSuccess={(sale) => {
          setCompletedSale(sale);
          setCart([]);
          setSelectedCustomer(null);
          setIsReceiptModalOpen(true);
        }}
      />

      <ReceiptModal
        isOpen={isReceiptModalOpen}
        sale={completedSale}
        onClose={() => setIsReceiptModalOpen(false)}
      />

      <HotkeyHelpModal
        isOpen={isHotkeyHelpOpen}
        onClose={() => setIsHotkeyHelpOpen(false)}
      />
    </div>
  );
}
