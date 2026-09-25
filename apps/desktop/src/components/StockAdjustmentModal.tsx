import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Package, Check, Loader2, X } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/apiClient";
import { useAuthStore } from "@/store/useAuthStore";
import { ProductDetail } from "@/pages/ProductsView";

const StockMovementSchema = z.object({
  product_id: z.string().min(1, "Selecione um produto"),
  movement_type: z.string().min(1, "Selecione o tipo de movimentação"),
  quantity: z.coerce.number().min(0.001, "Informe uma quantidade válida"),
  unit_cost: z.coerce.number().optional(),
  reference_doc: z.string().optional(),
  notes: z.string().optional(),
});

type StockFormValues = z.infer<typeof StockMovementSchema>;

interface StockAdjustmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  products: ProductDetail[];
}

export function StockAdjustmentModal({ isOpen, onClose, onSuccess, products }: StockAdjustmentModalProps) {
  const { token, activeCompany } = useAuthStore();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<StockFormValues>({
    resolver: zodResolver(StockMovementSchema),
    defaultValues: {
      product_id: "",
      movement_type: "AJUSTE_ENTRADA",
      quantity: 1,
      unit_cost: 0,
      reference_doc: "",
      notes: "",
    },
  });

  const selectedProductId = watch("product_id");
  const selectedProduct = products.find((p) => p.id === selectedProductId);

  useEffect(() => {
    if (isOpen) {
      reset({
        product_id: products[0]?.id || "",
        movement_type: "AJUSTE_ENTRADA",
        quantity: 1,
        unit_cost: 0,
        reference_doc: "",
        notes: "",
      });
      setErrorMessage(null);
    }
  }, [isOpen, reset, products]);

  if (!isOpen) return null;

  const onSubmit = async (values: StockFormValues) => {
    if (!activeCompany || !token) {
      setErrorMessage("Sessão ou empresa ativa não encontrada");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const payload = {
        company_id: activeCompany.id,
        product_id: values.product_id,
        movement_type: values.movement_type,
        quantity: values.quantity,
        unit_cost: values.unit_cost || null,
        reference_doc: values.reference_doc || null,
        notes: values.notes || null,
      };

      await apiFetch("/stock/movements", {
        method: "POST",
        body: JSON.stringify(payload),
      }, token);

      onSuccess();
      onClose();
    } catch (err: any) {
      setErrorMessage(err.message || "Erro ao registrar movimentação de estoque");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in-50">
      <Card className="w-full max-w-xl border-border/80 shadow-2xl bg-card overflow-hidden">
        <CardHeader className="bg-muted/40 border-b border-border pb-4 flex flex-row items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="h-9 w-9 rounded-lg bg-blue-500/10 text-blue-500 border border-blue-500/20 flex items-center justify-center font-bold">
              <Package className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-lg font-bold tracking-tight">Movimentação / Ajuste de Estoque</CardTitle>
              <CardDescription className="text-xs">
                Registre entradas, saídas manuais ou ajustes auditáveis com histórico imutável
              </CardDescription>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8">
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>

        <CardContent className="p-6">
          {errorMessage && (
            <div className="p-3 mb-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-xs">
              {errorMessage}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="product_id">Produto Selecionado *</Label>
              <select
                id="product_id"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2"
                {...register("product_id")}
              >
                <option value="">Selecione um produto...</option>
                {products.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.code ? `[${p.code}] ` : ""}{p.name} (Saldo Atual: {Number(p.stock_qty).toLocaleString("pt-BR")} {p.unit?.code || "UN"})
                  </option>
                ))}
              </select>
              {errors.product_id && <p className="text-xs text-destructive">{errors.product_id.message}</p>}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="movement_type">Tipo de Movimentação *</Label>
                <select
                  id="movement_type"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 font-medium"
                  {...register("movement_type")}
                >
                  <option value="AJUSTE_ENTRADA">➕ Ajuste Manual de Entrada</option>
                  <option value="ENTRADA_NF">📦 Entrada por NF / Fornecedor</option>
                  <option value="AJUSTE_SAIDA">➖ Ajuste Manual de Saída</option>
                  <option value="SAIDA_VENDA">🛒 Saída por Venda</option>
                </select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="quantity">Quantidade *</Label>
                <Input id="quantity" type="number" step="0.001" placeholder="1.000" {...register("quantity")} />
                {errors.quantity && <p className="text-xs text-destructive">{errors.quantity.message}</p>}
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="unit_cost">Custo Unitário (R$)</Label>
                <Input id="unit_cost" type="number" step="0.01" placeholder="0.00" {...register("unit_cost")} />
              </div>

              <div className="space-y-2">
                <Label htmlFor="reference_doc">Documento / Ref. (NF, Pedido)</Label>
                <Input id="reference_doc" placeholder="Ex: NF-10492" {...register("reference_doc")} />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="notes">Motivo / Observação da Auditoria</Label>
              <Input id="notes" placeholder="Ex: Contagem física de estoque ou compra" {...register("notes")} />
            </div>

            {selectedProduct && (
              <div className="p-3 rounded-lg bg-muted/40 border text-xs space-y-1">
                <div className="font-semibold text-foreground">Resumo do Estoque:</div>
                <div className="flex justify-between text-muted-foreground font-mono">
                  <span>Saldo Atual: {Number(selectedProduct.stock_qty).toLocaleString("pt-BR")} {selectedProduct.unit?.code || "UN"}</span>
                  <span>Preço de Venda: R$ {Number(selectedProduct.price).toFixed(2)}</span>
                </div>
              </div>
            )}

            <div className="pt-4 flex justify-end gap-3 border-t">
              <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting}>
                Cancelar
              </Button>
              <Button type="submit" className="gap-2 bg-blue-600 hover:bg-blue-700 text-white" disabled={isSubmitting}>
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" /> Processando...
                  </>
                ) : (
                  <>
                    <Check className="h-4 w-4" /> Registrar Movimentação
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
