import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Package, Barcode, Check, Loader2, X, Edit3 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/apiClient";
import { useAuthStore } from "@/store/useAuthStore";
import { ProductDetail } from "@/pages/ProductsView";

const ProductSchema = z.object({
  name: z.string().min(1, "Informe o nome do produto"),
  code: z.string().optional(),
  barcode: z.string().optional(),
  price: z.coerce.number().min(0.01, "Informe o preço de venda"),
  cost: z.coerce.number().min(0, "O custo deve ser positivo"),
  stock_qty: z.coerce.number().min(0, "A quantidade de estoque deve ser positiva"),
  min_stock_qty: z.coerce.number().min(0, "O estoque mínimo deve ser positivo"),
  category_id: z.string().optional(),
  unit_id: z.string().optional(),
});

type ProductFormValues = z.infer<typeof ProductSchema>;

interface ProductModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  categories: Array<{ id: string; name: string }>;
  units: Array<{ id: string; code: string; name: string }>;
  productToEdit?: ProductDetail | null;
}

export function ProductModal({
  isOpen,
  onClose,
  onSuccess,
  categories,
  units,
  productToEdit,
}: ProductModalProps) {
  const { token, user, activeCompany } = useAuthStore();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const isEditMode = !!productToEdit;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ProductFormValues>({
    resolver: zodResolver(ProductSchema),
    defaultValues: {
      name: "",
      code: "",
      barcode: "",
      price: 0,
      cost: 0,
      stock_qty: 0,
      min_stock_qty: 0,
    },
  });

  useEffect(() => {
    if (isOpen) {
      if (productToEdit) {
        const firstBarcode =
          productToEdit.barcodes && productToEdit.barcodes.length > 0
            ? productToEdit.barcodes[0].barcode
            : "";

        reset({
          name: productToEdit.name,
          code: productToEdit.code || "",
          barcode: firstBarcode,
          price: productToEdit.price,
          cost: productToEdit.cost,
          stock_qty: productToEdit.stock_qty,
          min_stock_qty: productToEdit.min_stock_qty,
          category_id: productToEdit.category?.id || "",
          unit_id: productToEdit.unit?.id || "",
        });
      } else {
        reset({
          name: "",
          code: "",
          barcode: "",
          price: 0,
          cost: 0,
          stock_qty: 0,
          min_stock_qty: 0,
          category_id: "",
          unit_id: "",
        });
      }
      setErrorMessage(null);
    }
  }, [isOpen, productToEdit, reset]);

  if (!isOpen) return null;

  const onSubmit = async (values: ProductFormValues) => {
    if (!user || !activeCompany || !token) {
      setErrorMessage("Sessão ou empresa ativa não encontrada");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      if (isEditMode && productToEdit) {
        // PUT update existing product
        const payload = {
          category_id: values.category_id || null,
          unit_id: values.unit_id || null,
          code: values.code || null,
          name: values.name,
          price: values.price,
          cost: values.cost,
          stock_qty: values.stock_qty,
          min_stock_qty: values.min_stock_qty,
          barcodes: values.barcode ? [values.barcode.trim()] : [],
        };

        await apiFetch(`/products/${productToEdit.id}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        }, token);
      } else {
        // POST create new product
        const payload = {
          tenant_id: user.tenant_id,
          company_id: activeCompany.id,
          category_id: values.category_id || null,
          unit_id: values.unit_id || null,
          code: values.code || null,
          name: values.name,
          price: values.price,
          cost: values.cost,
          stock_qty: values.stock_qty,
          min_stock_qty: values.min_stock_qty,
          barcodes: values.barcode ? [values.barcode.trim()] : [],
          is_active: true,
        };

        await apiFetch("/products", {
          method: "POST",
          body: JSON.stringify(payload),
        }, token);
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      setErrorMessage(err.message || "Erro ao salvar produto");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in-50">
      <Card className="w-full max-w-2xl border-border/80 shadow-2xl bg-card overflow-hidden">
        <CardHeader className="bg-muted/40 border-b border-border pb-4 flex flex-row items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="h-9 w-9 rounded-lg bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 flex items-center justify-center font-bold">
              {isEditMode ? <Edit3 className="h-5 w-5" /> : <Package className="h-5 w-5" />}
            </div>
            <div>
              <CardTitle className="text-lg font-bold tracking-tight">
                {isEditMode ? "Editar Produto" : "Cadastrar Novo Produto"}
              </CardTitle>
              <CardDescription className="text-xs">
                {isEditMode
                  ? `Atualizar dados do produto ${productToEdit?.name}`
                  : "Informe o nome, código de barras, preços e controle de estoque"}
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
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="sm:col-span-2 space-y-2">
                <Label htmlFor="name">Nome do Produto *</Label>
                <Input id="name" placeholder="Ex: Refrigerante Coca-Cola 2L" {...register("name")} />
                {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="code">SKU / Código Interno</Label>
                <Input id="code" placeholder="Ex: BEB-001" {...register("code")} />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="barcode">Código de Barras (EAN-13)</Label>
                <div className="relative">
                  <Barcode className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input id="barcode" placeholder="789..." className="pl-9 font-mono" {...register("barcode")} />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="category_id">Categoria</Label>
                <select
                  id="category_id"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  {...register("category_id")}
                >
                  <option value="">Selecione uma categoria...</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="unit_id">Unidade</Label>
                <select
                  id="unit_id"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  {...register("unit_id")}
                >
                  <option value="">UN (Unidade)</option>
                  {units.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.code} - {u.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2 border-t">
              <div className="space-y-2">
                <Label htmlFor="price">Preço Venda (R$) *</Label>
                <Input id="price" type="number" step="0.01" placeholder="0.00" {...register("price")} />
                {errors.price && <p className="text-xs text-destructive">{errors.price.message}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="cost">Preço Custo (R$)</Label>
                <Input id="cost" type="number" step="0.01" placeholder="0.00" {...register("cost")} />
              </div>

              <div className="space-y-2">
                <Label htmlFor="stock_qty">Estoque Atual</Label>
                <Input id="stock_qty" type="number" step="0.001" placeholder="0.000" {...register("stock_qty")} />
              </div>

              <div className="space-y-2">
                <Label htmlFor="min_stock_qty">Estoque Mínimo</Label>
                <Input id="min_stock_qty" type="number" step="0.001" placeholder="0.000" {...register("min_stock_qty")} />
              </div>
            </div>

            <div className="pt-4 flex justify-end gap-3 border-t">
              <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting}>
                Cancelar
              </Button>
              <Button type="submit" className="gap-2 bg-emerald-600 hover:bg-emerald-700 text-white" disabled={isSubmitting}>
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" /> Salvando...
                  </>
                ) : (
                  <>
                    <Check className="h-4 w-4" /> {isEditMode ? "Salvar Alterações" : "Salvar Produto"}
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
