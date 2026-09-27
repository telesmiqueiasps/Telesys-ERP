import { useState, useEffect } from "react";
import {
  ShoppingBag,
  Plus,
  Search,
  RefreshCw,
  CheckCircle2,
  XCircle,
  FileText,
  FileCode,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { PurchaseDetail } from "@/types/purchase";
import { purchaseService } from "@/services/purchaseService";
import { PurchaseModal } from "@/components/PurchaseModal";
import { XmlImporterModal } from "@/components/XmlImporterModal";
import { useAuthStore } from "@/store/useAuthStore";

export function PurchasesView() {
  const { activeCompany } = useAuthStore();
  const [purchases, setPurchases] = useState<PurchaseDetail[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  const [isNewPurchaseModalOpen, setIsNewPurchaseModalOpen] = useState<boolean>(false);
  const [isXmlModalOpen, setIsXmlModalOpen] = useState<boolean>(false);
  const [selectedPurchase, setSelectedPurchase] = useState<PurchaseDetail | null>(null);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPurchases = async () => {
    if (!activeCompany) return;
    setLoading(true);
    setError(null);
    try {
      const data = await purchaseService.getPurchases(activeCompany.id);
      setPurchases(data);
    } catch (err: any) {
      console.error("Erro ao carregar lista de compras:", err);
      setError("Falha ao carregar compras e entradas de mercadorias.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPurchases();
  }, [activeCompany]);

  const handleCancelPurchase = async (purchaseId: string) => {
    if (!window.confirm("Tem certeza que deseja cancelar esta entrada de compra? O estoque dos produtos será estornado automaticamente.")) {
      return;
    }

    setActionLoading(true);
    try {
      await purchaseService.cancelPurchase(purchaseId);
      await fetchPurchases();
      if (selectedPurchase?.id === purchaseId) {
        setSelectedPurchase(null);
      }
    } catch (err: any) {
      alert(err?.message || "Erro ao cancelar compra.");
    } finally {
      setActionLoading(false);
    }
  };

  const filteredPurchases = purchases.filter((p) => {
    const matchesSearch =
      p.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (p.supplier_name && p.supplier_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (p.notes && p.notes.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesStatus =
      statusFilter === "ALL" || p.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "RECEIVED":
        return (
          <Badge variant="success" className="gap-1">
            <CheckCircle2 className="h-3 w-3" /> Recebido / Concluído
          </Badge>
        );
      case "CANCELED":
        return (
          <Badge variant="destructive" className="gap-1">
            <XCircle className="h-3 w-3" /> Cancelado
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Bar Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight flex items-center gap-2">
            <ShoppingBag className="h-6 w-6 text-primary" /> Compras & Entradas de Mercadorias
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Registro de entradas de fornecedores com atualização automática de estoque e custos
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => setIsXmlModalOpen(true)}
            className="gap-2 text-xs h-9 font-semibold border-primary/40 text-primary hover:bg-primary/10"
          >
            <FileCode className="h-4 w-4" /> Importar XML da NF-e
          </Button>

          <Button
            onClick={() => setIsNewPurchaseModalOpen(true)}
            className="gap-2 bg-primary hover:bg-primary/90 text-xs h-9 font-semibold"
          >
            <Plus className="h-4 w-4" /> Nova Entrada Avulsa
          </Button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="p-4 bg-card border border-border rounded-xl shadow-sm space-y-3">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex flex-1 items-center gap-2 w-full">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar por código (COMP-...), fornecedor ou nota fiscal..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9 h-9 text-xs"
              />
            </div>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-9 rounded-md border border-input bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="ALL">Todos os Status</option>
              <option value="RECEIVED">Recebido / Concluído</option>
              <option value="CANCELED">Cancelado</option>
            </select>
          </div>

          <Button variant="outline" size="sm" onClick={fetchPurchases} disabled={loading} className="gap-1.5 text-xs h-9">
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Atualizar
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-xs flex items-center justify-between">
          <span>{error}</span>
          <Button variant="ghost" size="sm" onClick={fetchPurchases} className="h-6 text-[10px] px-2">Tentar Novamente</Button>
        </div>
      )}

      {/* Purchases Table */}
      <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-muted-foreground flex flex-col items-center justify-center space-y-2">
            <RefreshCw className="h-6 w-6 animate-spin text-primary" />
            <span>Carregando entradas de compras...</span>
          </div>
        ) : filteredPurchases.length === 0 ? (
          <div className="p-12 text-center text-xs text-muted-foreground flex flex-col items-center justify-center space-y-2">
            <ShoppingBag className="h-10 w-10 text-muted-foreground/50" />
            <span className="font-semibold text-foreground text-sm">Nenhuma compra registrada</span>
            <span>Utilize o botão "+ Nova Entrada de Compra" para dar entrada em mercadorias.</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-muted/60 text-muted-foreground border-b border-border font-medium">
                <tr>
                  <th className="p-3">Código</th>
                  <th className="p-3">Data/Hora</th>
                  <th className="p-3">Fornecedor</th>
                  <th className="p-3">Operador</th>
                  <th className="p-3 text-center">Status</th>
                  <th className="p-3 text-center">Itens</th>
                  <th className="p-3 text-right">Total (R$)</th>
                  <th className="p-3 text-center">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredPurchases.map((purchase) => (
                  <tr key={purchase.id} className="hover:bg-muted/30 transition-colors">
                    <td className="p-3 font-mono font-bold text-foreground">{purchase.code}</td>
                    <td className="p-3 text-muted-foreground font-mono">
                      {new Date(purchase.created_at).toLocaleString("pt-BR")}
                    </td>
                    <td className="p-3 font-medium text-foreground">
                      {purchase.supplier_name || <span className="text-muted-foreground italic">Entrada Avulsa</span>}
                    </td>
                    <td className="p-3 text-muted-foreground">{purchase.user_name || "Sistema"}</td>
                    <td className="p-3 text-center">{getStatusBadge(purchase.status)}</td>
                    <td className="p-3 text-center font-mono font-semibold">{purchase.items.length}</td>
                    <td className="p-3 text-right font-mono font-extrabold text-emerald-600 dark:text-emerald-400">
                      R$ {purchase.total_amount.toFixed(2)}
                    </td>
                    <td className="p-3 text-center">
                      <div className="flex items-center justify-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setSelectedPurchase(purchase)}
                          className="h-7 text-xs px-2 gap-1 text-primary hover:text-primary hover:bg-primary/10"
                        >
                          <FileText className="h-3.5 w-3.5" /> Detalhes
                        </Button>

                        {purchase.status !== "CANCELED" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleCancelPurchase(purchase.id)}
                            disabled={actionLoading}
                            className="h-7 text-xs px-2 gap-1 text-destructive hover:text-destructive hover:bg-destructive/10"
                          >
                            <XCircle className="h-3.5 w-3.5" /> Cancelar
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal Nova Compra */}
      <PurchaseModal
        isOpen={isNewPurchaseModalOpen}
        onClose={() => setIsNewPurchaseModalOpen(false)}
        onSuccess={() => {
          fetchPurchases();
        }}
      />

      {/* Modal Importar XML da NF-e */}
      <XmlImporterModal
        isOpen={isXmlModalOpen}
        onClose={() => setIsXmlModalOpen(false)}
        onSuccess={() => {
          fetchPurchases();
        }}
      />

      {/* Modal Detalhes da Compra */}
      {selectedPurchase && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-2xl overflow-hidden animate-in fade-in zoom-in duration-200 flex flex-col max-h-[85vh]">
            <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-muted/40">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold font-mono text-sm">
                  {selectedPurchase.code.slice(-4)}
                </div>
                <div>
                  <h2 className="text-base font-bold text-foreground">Entrada de Compra #{selectedPurchase.code}</h2>
                  <p className="text-xs text-muted-foreground">
                    Registrado em {new Date(selectedPurchase.created_at).toLocaleString("pt-BR")}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {getStatusBadge(selectedPurchase.status)}
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-muted-foreground hover:text-foreground"
                  onClick={() => setSelectedPurchase(null)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div className="p-6 space-y-4 overflow-y-auto flex-1">
              <div className="grid grid-cols-2 gap-4 p-3 bg-muted/30 rounded-lg border border-border text-xs">
                <div>
                  <span className="text-muted-foreground block">Fornecedor:</span>
                  <span className="font-semibold text-foreground">
                    {selectedPurchase.supplier_name || "Entrada Avulsa"}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground block">Operador Responsável:</span>
                  <span className="font-semibold text-foreground">{selectedPurchase.user_name || "Sistema"}</span>
                </div>
                {selectedPurchase.notes && (
                  <div className="col-span-2 pt-2 border-t border-border">
                    <span className="text-muted-foreground block">Observações / NF:</span>
                    <span className="text-foreground">{selectedPurchase.notes}</span>
                  </div>
                )}
              </div>

              <span className="text-xs font-bold text-foreground block">Itens da Entrada</span>
              <div className="border border-border rounded-lg overflow-hidden">
                <table className="w-full text-xs text-left">
                  <thead className="bg-muted/60 text-muted-foreground font-medium border-b border-border">
                    <tr>
                      <th className="p-2.5">Item</th>
                      <th className="p-2.5">Produto</th>
                      <th className="p-2.5 text-right">Qtd</th>
                      <th className="p-2.5 text-right">Custo Unit. (R$)</th>
                      <th className="p-2.5 text-right">Total (R$)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {selectedPurchase.items.map((item) => (
                      <tr key={item.id} className="hover:bg-muted/30">
                        <td className="p-2.5 font-mono text-muted-foreground">{item.item_number}</td>
                        <td className="p-2.5 font-medium text-foreground">{item.product_name}</td>
                        <td className="p-2.5 text-right font-mono">{item.quantity} {item.unit_code}</td>
                        <td className="p-2.5 text-right font-mono">R$ {item.unit_cost.toFixed(2)}</td>
                        <td className="p-2.5 text-right font-mono font-bold text-emerald-600 dark:text-emerald-400">
                          R$ {item.total_cost.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="p-3 bg-muted/40 rounded-lg border border-border flex items-center justify-between text-xs">
                <div>
                  <span className="text-muted-foreground">Subtotal: </span>
                  <span className="font-mono font-semibold">R$ {selectedPurchase.subtotal.toFixed(2)}</span>
                  {selectedPurchase.discount_amount > 0 && (
                    <span className="text-rose-500 font-mono ml-2">
                      (- R$ {selectedPurchase.discount_amount.toFixed(2)})
                    </span>
                  )}
                </div>

                <div>
                  <span className="text-muted-foreground">Total da Compra: </span>
                  <span className="font-mono text-base font-extrabold text-emerald-600 dark:text-emerald-400">
                    R$ {selectedPurchase.total_amount.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
