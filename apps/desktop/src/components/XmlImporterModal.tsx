import React, { useState, useEffect } from "react";
import {
  X,
  FileCode,
  Upload,
  CheckCircle2,
  AlertCircle,
  Link,
  PlusCircle,
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Product } from "@/types/product";
import { NfeParseResponse, NfeConfirmItemInput } from "@/types/xmlImport";
import { purchaseService } from "@/services/purchaseService";
import { productService } from "@/services/productService";
import { syncEngine } from "@/services/syncEngine";
import { useAuthStore } from "@/store/useAuthStore";

interface XmlImporterModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function XmlImporterModal({ isOpen, onClose, onSuccess }: XmlImporterModalProps) {
  const { activeCompany } = useAuthStore();
  const [step, setStep] = useState<1 | 2>(1);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [parsedData, setParsedData] = useState<NfeParseResponse | null>(null);
  const [companyProducts, setCompanyProducts] = useState<Product[]>([]);

  // Item match actions map: item_number -> NfeConfirmItemInput
  const [itemInputs, setItemInputs] = useState<Record<number, NfeConfirmItemInput>>({});
  const [generatePayables, setGeneratePayables] = useState<boolean>(true);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !activeCompany) return;

    const fetchProducts = async () => {
      try {
        const prods = await productService.getProducts(activeCompany.id);
        setCompanyProducts(prods);
      } catch (err) {
        console.error("Erro ao carregar catálogo para vinculação:", err);
      }
    };

    fetchProducts();
    setStep(1);
    setSelectedFile(null);
    setParsedData(null);
    setItemInputs({});
    setGeneratePayables(true);
    setLoading(false);
    setError(null);
  }, [isOpen, activeCompany]);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUploadParse = async () => {
    if (!selectedFile) {
      setError("Selecione um arquivo .xml de NF-e.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await purchaseService.parseNfeXml(selectedFile, activeCompany?.id);
      setParsedData(result);

      // Iniciar mapa de ações para cada item
      const initialMap: Record<number, NfeConfirmItemInput> = {};
      result.items.forEach((item) => {
        const isMatched = !!item.matched_product_id;
        initialMap[item.item_number] = {
          item_number: item.item_number,
          cProd: item.cProd,
          cEAN: item.cEAN,
          name: item.xProd,
          ncm: item.ncm,
          uCom: item.uCom,
          quantity: item.qCom,
          unit_cost: item.vUnCom,
          action: isMatched ? "LINK_EXISTING" : "CREATE_NEW",
          linked_product_id: item.matched_product_id || null,
        };
      });

      setItemInputs(initialMap);
      setStep(2);
    } catch (err: any) {
      console.error("Erro ao analisar arquivo XML:", err);
      setError(err?.message || "Falha ao processar o arquivo XML de NF-e.");
    } finally {
      setLoading(false);
    }
  };

  const handleItemActionChange = (itemNumber: number, action: "CREATE_NEW" | "LINK_EXISTING", linkedProductId?: string) => {
    setItemInputs((prev) => ({
      ...prev,
      [itemNumber]: {
        ...prev[itemNumber],
        action,
        linked_product_id: action === "LINK_EXISTING" ? linkedProductId || prev[itemNumber].linked_product_id : null,
      },
    }));
  };

  const handleConfirmImport = async () => {
    if (!parsedData) return;

    setLoading(true);
    setError(null);

    try {
      const itemsPayload = Object.values(itemInputs);

      const purchase = await purchaseService.confirmNfeXml(
        {
          chNFe: parsedData.chNFe,
          nNF: parsedData.nNF,
          supplier: parsedData.supplier,
          items: itemsPayload,
          duplicatas: parsedData.duplicatas,
          generate_payables: generatePayables,
        },
        activeCompany?.id
      );

      // Registrar evento na sync engine local-first
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
            nNF: parsedData.nNF,
            total_amount: purchase.total_amount,
            items_count: purchase.items.length,
          },
        });
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      console.error("Erro ao confirmar importação da NF-e:", err);
      setError(err?.message || "Falha ao concluir a importação da NF-e.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-4xl overflow-hidden animate-in fade-in zoom-in duration-200 flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-muted/40">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold">
              <FileCode className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-foreground">Importador de NF-e via XML</h2>
              <p className="text-xs text-muted-foreground">
                Entrada automática de fornecedor, produtos, estoque e contas a pagar
              </p>
            </div>
          </div>

          <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-foreground" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-4 overflow-y-auto flex-1">
          {error && (
            <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-xs flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {step === 1 ? (
            /* Passo 1: Seleção de Arquivo XML */
            <div className="py-8 flex flex-col items-center justify-center space-y-4 text-center">
              <div className="h-16 w-16 rounded-full bg-primary/10 text-primary flex items-center justify-center">
                <Upload className="h-8 w-8" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-foreground">Selecione o arquivo XML da Nota Fiscal Eletrônica</h3>
                <p className="text-xs text-muted-foreground max-w-md mt-1">
                  O sistema lerá os dados do fornecedor, os produtos adquiridos e as duplicatas financeiras.
                </p>
              </div>

              <div className="w-full max-w-md">
                <input
                  type="file"
                  accept=".xml"
                  onChange={handleFileChange}
                  className="w-full text-xs text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-primary file:text-primary-foreground hover:file:bg-primary/90 cursor-pointer"
                />
              </div>

              {selectedFile && (
                <div className="p-3 bg-muted/40 rounded-lg border border-border text-xs flex items-center gap-2">
                  <FileCode className="h-4 w-4 text-primary" />
                  <span className="font-semibold">{selectedFile.name}</span>
                  <span className="text-muted-foreground">({(selectedFile.size / 1024).toFixed(1)} KB)</span>
                </div>
              )}

              <Button
                onClick={handleUploadParse}
                disabled={!selectedFile || loading}
                className="gap-2 bg-primary hover:bg-primary/90 text-xs h-9 px-6 font-semibold"
              >
                {loading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
                {loading ? "Processando XML..." : "Analisar Arquivo XML"}
              </Button>
            </div>
          ) : (
            /* Passo 2: Conferência e Vínculo de Produtos */
            parsedData && (
              <div className="space-y-4">
                {/* Visual Resumo da NF-e */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 p-3 bg-muted/30 border border-border rounded-lg text-xs">
                  <div>
                    <span className="text-muted-foreground block">Fornecedor / Emitente:</span>
                    <span className="font-bold text-foreground">{parsedData.supplier.name}</span>
                    <span className="text-[10px] text-muted-foreground block">CNPJ: {parsedData.supplier.document}</span>
                  </div>

                  <div>
                    <span className="text-muted-foreground block">Dados do Documento:</span>
                    <span className="font-bold text-foreground">NF-e Nº {parsedData.nNF} (Série {parsedData.serie})</span>
                    <span className="text-[10px] text-muted-foreground block font-mono truncate">Chave: {parsedData.chNFe}</span>
                  </div>

                  <div className="text-right">
                    <span className="text-muted-foreground block">Valor Total da Nota:</span>
                    <span className="text-lg font-extrabold font-mono text-emerald-600 dark:text-emerald-400">
                      R$ {parsedData.total_vNF.toFixed(2)}
                    </span>
                  </div>
                </div>

                {/* Tabela de Vínculo de Itens */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-foreground">Vínculo dos Produtos ({parsedData.items.length} itens)</span>
                    <span className="text-[11px] text-muted-foreground">
                      Defina se deseja criar um novo produto ou vincular a um produto existente no catálogo local.
                    </span>
                  </div>

                  <div className="border border-border rounded-lg overflow-hidden max-h-[260px] overflow-y-auto">
                    <table className="w-full text-xs text-left">
                      <thead className="bg-muted/60 text-muted-foreground sticky top-0 font-medium">
                        <tr>
                          <th className="p-2.5">Item</th>
                          <th className="p-2.5">Produto no XML</th>
                          <th className="p-2.5 text-right">Qtd / Un.</th>
                          <th className="p-2.5 text-right">Custo Unit. (R$)</th>
                          <th className="p-2.5">Ação de Vínculo no Estoque</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border">
                        {parsedData.items.map((item) => {
                          const currentAction = itemInputs[item.item_number]?.action || "CREATE_NEW";
                          const currentLinkedId = itemInputs[item.item_number]?.linked_product_id || "";

                          return (
                            <tr key={item.item_number} className="hover:bg-muted/30 transition-colors">
                              <td className="p-2.5 font-mono text-muted-foreground">{item.item_number}</td>
                              <td className="p-2.5">
                                <span className="font-semibold text-foreground block">{item.xProd}</span>
                                <span className="text-[10px] text-muted-foreground font-mono">
                                  Cód: {item.cProd} {item.cEAN ? `| EAN: ${item.cEAN}` : ""}
                                </span>
                              </td>
                              <td className="p-2.5 text-right font-mono font-semibold">
                                {item.qCom} {item.uCom}
                              </td>
                              <td className="p-2.5 text-right font-mono font-bold">R$ {item.vUnCom.toFixed(2)}</td>
                              <td className="p-2.5">
                                <div className="space-y-1">
                                  <div className="flex items-center gap-3">
                                    <label className="flex items-center gap-1 cursor-pointer">
                                      <input
                                        type="radio"
                                        name={`action_${item.item_number}`}
                                        checked={currentAction === "CREATE_NEW"}
                                        onChange={() => handleItemActionChange(item.item_number, "CREATE_NEW")}
                                        className="text-primary focus:ring-primary"
                                      />
                                      <span className="text-[11px] font-medium flex items-center gap-1 text-primary">
                                        <PlusCircle className="h-3 w-3" /> Criar Novo
                                      </span>
                                    </label>

                                    <label className="flex items-center gap-1 cursor-pointer">
                                      <input
                                        type="radio"
                                        name={`action_${item.item_number}`}
                                        checked={currentAction === "LINK_EXISTING"}
                                        onChange={() => handleItemActionChange(item.item_number, "LINK_EXISTING")}
                                        className="text-primary focus:ring-primary"
                                      />
                                      <span className="text-[11px] font-medium flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
                                        <Link className="h-3 w-3" /> Vincular Existente
                                      </span>
                                    </label>
                                  </div>

                                  {currentAction === "LINK_EXISTING" && (
                                    <select
                                      value={currentLinkedId}
                                      onChange={(e) => handleItemActionChange(item.item_number, "LINK_EXISTING", e.target.value)}
                                      className="w-full h-8 rounded border border-input bg-background px-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                                    >
                                      <option value="">Selecione o Produto Local...</option>
                                      {companyProducts.map((p) => (
                                        <option key={p.id} value={p.id}>
                                          {p.name} (Estoque: {p.stock_qty})
                                        </option>
                                      ))}
                                    </select>
                                  )}
                                </div>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Seção Financeira / Duplicatas */}
                {parsedData.duplicatas.length > 0 && (
                  <div className="p-3 bg-muted/40 border border-border rounded-lg space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={generatePayables}
                          onChange={(e) => setGeneratePayables(e.target.checked)}
                          className="rounded text-primary focus:ring-primary"
                        />
                        <span className="text-xs font-bold text-foreground">
                          Gerar automaticamente {parsedData.duplicatas.length} Conta(s) a Pagar no Financeiro
                        </span>
                      </label>
                    </div>

                    {generatePayables && (
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1">
                        {parsedData.duplicatas.map((dup, idx) => (
                          <div key={idx} className="p-2 rounded bg-background border border-border text-xs flex justify-between">
                            <span className="text-muted-foreground">Dup {dup.nDup}:</span>
                            <span className="font-mono text-muted-foreground">
                              Venc: {new Date(dup.dVenc).toLocaleDateString("pt-BR")}
                            </span>
                            <span className="font-mono font-bold text-rose-500">R$ {dup.vDup.toFixed(2)}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Footer Controls */}
                <div className="pt-2 flex items-center justify-between border-t border-border">
                  <Button variant="outline" size="sm" onClick={() => setStep(1)} className="text-xs">
                    Voltar ao Arquivo
                  </Button>

                  <Button
                    onClick={handleConfirmImport}
                    disabled={loading}
                    className="gap-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs h-9 px-6 font-bold"
                  >
                    <CheckCircle2 className="h-4 w-4" />
                    {loading ? "Importando e Atualizando Estoque..." : "Confirmar Importação de NF-e"}
                  </Button>
                </div>
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
}
