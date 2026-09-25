import { X, Keyboard } from "lucide-react";
import { Button } from "@/components/ui/button";

interface HotkeyHelpModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function HotkeyHelpModal({ isOpen, onClose }: HotkeyHelpModalProps) {
  if (!isOpen) return null;

  const hotkeys = [
    { key: "F1", description: "Abrir esta tela de Ajuda / Atalhos" },
    { key: "F2", description: "Iniciar Nova Venda (Limpar Carrinho)" },
    { key: "F3 / Barra", description: "Focar na busca de produto / Leitor de Código de Barras" },
    { key: "F4", description: "Selecionar / Identificar Cliente na venda" },
    { key: "F8", description: "Aplicar Desconto Geral no Subtotal" },
    { key: "F9", description: "Remover / Cancelar Item Selecionado do Carrinho" },
    { key: "F10 / Enter", description: "Abrir Modal de Pagamento & Encerramento" },
    { key: "Esc", description: "Fechar Modais / Cancelar Seleção" },
  ];

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-muted/40">
          <div className="flex items-center gap-2">
            <Keyboard className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-bold">Atalhos de Teclado (PDV)</h2>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8 text-muted-foreground">
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="p-6 space-y-3">
          <div className="divide-y divide-border/60 border border-border/60 rounded-lg overflow-hidden">
            {hotkeys.map((hk, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-card hover:bg-muted/20">
                <span className="font-mono font-bold text-xs bg-primary/10 text-primary border border-primary/20 px-2 py-1 rounded">
                  {hk.key}
                </span>
                <span className="text-xs text-muted-foreground font-medium">{hk.description}</span>
              </div>
            ))}
          </div>

          <div className="pt-2 flex justify-end">
            <Button onClick={onClose} className="text-xs font-semibold">
              Entendido (Esc)
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
