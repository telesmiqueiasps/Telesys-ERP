import { X, Printer, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SaleDetail } from "@/types/sale";
import { useAuthStore } from "@/store/useAuthStore";

interface ReceiptModalProps {
  isOpen: boolean;
  sale: SaleDetail | null;
  onClose: () => void;
}

export function ReceiptModal({ isOpen, sale, onClose }: ReceiptModalProps) {
  const { activeCompany } = useAuthStore();

  if (!isOpen || !sale) return null;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in duration-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-muted/40">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-emerald-500" />
            <h2 className="text-lg font-bold">Venda Finalizada com Sucesso!</h2>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8 text-muted-foreground">
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Printable Receipt Area */}
        <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto font-mono text-xs" id="printable-receipt">
          {/* Header Store Info */}
          <div className="text-center space-y-1 border-b border-dashed border-border pb-3">
            <h3 className="font-bold text-sm text-foreground uppercase">{activeCompany?.name || "TELESYS ERP"}</h3>
            {activeCompany?.cnpj && <p>CNPJ: {activeCompany.cnpj}</p>}
            <p className="text-[11px] text-muted-foreground">COMPROVANTE NÃO-FISCAL DE VENDA</p>
            <p className="font-bold pt-1">{sale.code}</p>
            <p className="text-[10px]">{new Date(sale.created_at).toLocaleString("pt-BR")}</p>
          </div>

          {/* Customer info if specified */}
          {sale.customer_name && (
            <div className="border-b border-dashed border-border pb-2 text-[11px]">
              <span className="font-bold">Cliente:</span> {sale.customer_name}
            </div>
          )}

          {/* Items Table */}
          <div className="space-y-1 border-b border-dashed border-border pb-3">
            <div className="grid grid-cols-12 font-bold text-[11px] border-b border-border pb-1">
              <span className="col-span-6">ITEM / DESCRIÇÃO</span>
              <span className="col-span-2 text-center">QTD</span>
              <span className="col-span-4 text-right">TOTAL</span>
            </div>
            {sale.items.map((it, idx) => (
              <div key={idx} className="grid grid-cols-12 text-[11px] py-0.5">
                <span className="col-span-6 truncate font-sans">{it.product_name}</span>
                <span className="col-span-2 text-center font-mono">{Number(it.quantity)} {it.unit_code}</span>
                <span className="col-span-4 text-right font-mono">
                  R$ {Number(it.total_price).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                </span>
              </div>
            ))}
          </div>

          {/* Totals */}
          <div className="space-y-1 border-b border-dashed border-border pb-3 text-xs">
            <div className="flex justify-between">
              <span>SUBTOTAL:</span>
              <span>R$ {Number(sale.subtotal).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}</span>
            </div>
            {Number(sale.discount_amount) > 0 && (
              <div className="flex justify-between text-amber-500 font-bold">
                <span>DESCONTO:</span>
                <span>- R$ {Number(sale.discount_amount).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}</span>
              </div>
            )}
            <div className="flex justify-between font-bold text-sm pt-1 border-t border-border">
              <span>TOTAL PAGO:</span>
              <span className="text-emerald-500 font-extrabold">
                R$ {Number(sale.total_amount).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </span>
            </div>
          </div>

          {/* Payments */}
          <div className="space-y-1 text-[11px]">
            <span className="font-bold">FORMAS DE PAGAMENTO:</span>
            {sale.payments.map((p, i) => (
              <div key={i} className="flex justify-between pl-2">
                <span>{p.payment_method === "MONEY" ? "Dinheiro" : p.payment_method}:</span>
                <span>R$ {Number(p.amount).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}</span>
              </div>
            ))}
            {sale.payments.some((p) => Number(p.change_amount) > 0) && (
              <div className="flex justify-between pl-2 font-bold text-emerald-500">
                <span>TROCO:</span>
                <span>
                  R${" "}
                  {Number(
                    sale.payments.reduce((acc, p) => acc + Number(p.change_amount), 0)
                  ).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-border flex items-center justify-between bg-muted/40">
          <Button variant="outline" onClick={onClose}>
            Fechar (Esc)
          </Button>
          <Button onClick={handlePrint} className="gap-2 font-semibold bg-primary">
            <Printer className="h-4 w-4" /> Imprimir Comprovante
          </Button>
        </div>
      </div>
    </div>
  );
}
