import { useState, useEffect } from "react";
import {
  FileText,
  Plus,
  Trash2,
  Play,
  Layers,
  DollarSign,
  Package,
  RefreshCw,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  FiscalOperation,
  FiscalScenarioRuleInput,
  FiscalScenarioMatchResult,
} from "@/types/fiscal_operation";
import { fiscalOperationService } from "@/services/fiscalOperationService";
import { useAuthStore } from "@/store/useAuthStore";

export function FiscalOperationsSettingsCard() {
  const { activeCompany } = useAuthStore();
  const [operations, setOperations] = useState<FiscalOperation[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedOp, setSelectedOp] = useState<FiscalOperation | null>(null);

  // Form para nova regra
  const [isRuleModalOpen, setIsRuleModalOpen] = useState(false);
  const [ruleDescription, setRuleDescription] = useState("");
  const [ruleCfop, setRuleCfop] = useState("");
  const [ruleUfOrigin, setRuleUfOrigin] = useState("");
  const [ruleUfDest, setRuleUfDest] = useState("");
  const [ruleIsSameUf, setRuleIsSameUf] = useState<string>("any");
  const [ruleIsFinalConsumer, setRuleIsFinalConsumer] = useState<string>("any");
  const [ruleIsTaxContrib, setRuleIsTaxContrib] = useState<string>("any");
  const [ruleEffectiveFrom, setRuleEffectiveFrom] = useState(new Date().toISOString().split("T")[0]);
  const [ruleEffectiveTo, setRuleEffectiveTo] = useState("");
  const [rulePriority, setRulePriority] = useState<number>(10);

  // State para simulador de matching
  const [simUfOrigin, setSimUfOrigin] = useState("SP");
  const [simUfDest, setSimUfDest] = useState("SP");
  const [simFinalConsumer, setSimFinalConsumer] = useState(true);
  const [simTaxContrib, setSimTaxContrib] = useState(false);
  const [simDocModel, setSimDocModel] = useState("55");
  const [simOpCode, setSimOpCode] = useState("VENDA_ESTADO");
  const [simResult, setSimResult] = useState<FiscalScenarioMatchResult | null>(null);
  const [simulating, setSimulating] = useState(false);

  const fetchOperations = async () => {
    if (!activeCompany?.id) return;
    setLoading(true);
    try {
      const data = await fiscalOperationService.getOperations(activeCompany.id);
      setOperations(data);
      if (data.length > 0 && !selectedOp) {
        setSelectedOp(data[0]);
      }
    } catch (err: any) {
      console.error("Erro ao carregar operações fiscais:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOperations();
  }, [activeCompany?.id]);

  const handleAddRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCompany?.id || !selectedOp || !ruleDescription || !ruleCfop) return;

    try {
      const payload: FiscalScenarioRuleInput = {
        description: ruleDescription,
        cfop: ruleCfop,
        uf_origin: ruleUfOrigin ? ruleUfOrigin.toUpperCase() : null,
        uf_destination: ruleUfDest ? ruleUfDest.toUpperCase() : null,
        is_same_uf: ruleIsSameUf === "yes" ? true : ruleIsSameUf === "no" ? false : null,
        is_final_consumer: ruleIsFinalConsumer === "yes" ? true : ruleIsFinalConsumer === "no" ? false : null,
        is_tax_contributor: ruleIsTaxContrib === "yes" ? true : ruleIsTaxContrib === "no" ? false : null,
        effective_from: ruleEffectiveFrom,
        effective_to: ruleEffectiveTo || null,
        priority: Number(rulePriority) || 10,
        is_active: true,
      };

      await fiscalOperationService.addRule(activeCompany.id, selectedOp.id, payload);
      setIsRuleModalOpen(false);
      resetRuleForm();
      await fetchOperations();
    } catch (err: any) {
      alert("Erro ao adicionar regra: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    if (!activeCompany?.id || !confirm("Deseja realmente remover esta regra de cenário?")) return;
    try {
      await fiscalOperationService.deleteRule(activeCompany.id, ruleId);
      await fetchOperations();
    } catch (err: any) {
      alert("Erro ao remover regra: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleRunSimulator = async () => {
    if (!activeCompany?.id) return;
    setSimulating(true);
    try {
      const res = await fiscalOperationService.matchScenario(activeCompany.id, {
        operation_code: simOpCode || undefined,
        operation_type: "OUT",
        uf_origin: simUfOrigin,
        uf_destination: simUfDest,
        is_final_consumer: simFinalConsumer,
        is_tax_contributor: simTaxContrib,
        doc_model: simDocModel,
      });
      setSimResult(res);
    } catch (err: any) {
      alert("Erro na simulação: " + (err.response?.data?.detail || err.message));
    } finally {
      setSimulating(false);
    }
  };

  const resetRuleForm = () => {
    setRuleDescription("");
    setRuleCfop("");
    setRuleUfOrigin("");
    setRuleUfDest("");
    setRuleIsSameUf("any");
    setRuleIsFinalConsumer("any");
    setRuleIsTaxContrib("any");
    setRuleEffectiveFrom(new Date().toISOString().split("T")[0]);
    setRuleEffectiveTo("");
    setRulePriority(10);
  };

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <Card className="border-border/60 shadow-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
                <FileText className="h-6 w-6" />
              </div>
              <div>
                <CardTitle className="text-lg font-bold">Matriz de Operações Fiscais e Regras de CFOP</CardTitle>
                <CardDescription className="text-xs">
                  Resolução automatizada e versionada por UF, Consumidor Final, Contribuinte e Vigência.
                </CardDescription>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchOperations}
              className="gap-1.5 text-xs"
              disabled={loading}
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} /> Atualizar Operações
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Main Grid: Left Side Operations List, Right Side Rules & Simulator */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sidebar Operations */}
        <Card className="border-border/60 shadow-sm lg:col-span-1 space-y-4 p-4">
          <div className="flex items-center justify-between pb-2 border-b border-border/40">
            <h3 className="font-semibold text-sm flex items-center gap-2">
              <Layers className="h-4 w-4 text-primary" /> Operações Fiscais ({operations.length})
            </h3>
          </div>

          <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
            {operations.map((op) => {
              const isSelected = selectedOp?.id === op.id;
              return (
                <div
                  key={op.id}
                  onClick={() => setSelectedOp(op)}
                  className={`p-3 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? "bg-primary/10 border-primary/40 shadow-sm"
                      : "bg-card border-border/60 hover:border-border text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <div className="flex items-center justify-between font-bold text-xs text-foreground mb-1">
                    <span>{op.name}</span>
                    <Badge variant={op.operation_type === "OUT" ? "default" : "secondary"} className="text-[10px]">
                      {op.operation_type === "OUT" ? "Saída" : "Entrada"}
                    </Badge>
                  </div>

                  <div className="text-[11px] font-mono text-muted-foreground space-y-1">
                    <div>Código: <span className="font-semibold text-foreground">{op.code}</span></div>
                    <div className="flex items-center gap-2 pt-1 text-[10px]">
                      {op.affect_inventory && (
                        <span className="flex items-center gap-1 text-emerald-400">
                          <Package className="h-3 w-3" /> Estoque
                        </span>
                      )}
                      {op.affect_financial && (
                        <span className="flex items-center gap-1 text-blue-400">
                          <DollarSign className="h-3 w-3" /> Financeiro
                        </span>
                      )}
                      <span className="ml-auto bg-muted px-1.5 py-0.5 rounded text-foreground font-semibold">
                        {op.rules.length} regra(s)
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Right Side: Selected Operation Details + Rules */}
        <div className="lg:col-span-2 space-y-6">
          {selectedOp ? (
            <Card className="border-border/60 shadow-sm space-y-4 p-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border/40">
                <div>
                  <h3 className="text-base font-bold text-foreground flex items-center gap-2">
                    {selectedOp.name}
                    <Badge variant="outline" className="font-mono text-xs">
                      {selectedOp.code}
                    </Badge>
                  </h3>
                  <p className="text-xs text-muted-foreground">{selectedOp.description || "Sem descrição."}</p>
                </div>

                <Button
                  size="sm"
                  onClick={() => setIsRuleModalOpen(true)}
                  className="gap-1.5 text-xs self-start sm:self-auto"
                >
                  <Plus className="h-3.5 w-3.5" /> Adicionar Regra CFOP
                </Button>
              </div>

              {/* Rules List Table */}
              <div className="space-y-3">
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Regras Tributárias e Resolução de CFOP
                </h4>

                {selectedOp.rules.length === 0 ? (
                  <div className="p-8 text-center text-xs text-muted-foreground border border-dashed rounded-xl">
                    Nenhuma regra cadastrada para esta operação. Clique em "Adicionar Regra CFOP".
                  </div>
                ) : (
                  <div className="overflow-x-auto rounded-xl border border-border/60">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-muted/40 border-b border-border text-muted-foreground font-semibold uppercase">
                        <tr>
                          <th className="py-2.5 px-3">Prior.</th>
                          <th className="py-2.5 px-3">Descrição da Regra</th>
                          <th className="py-2.5 px-3">CFOP</th>
                          <th className="py-2.5 px-3">Condições (UF / Consumidor)</th>
                          <th className="py-2.5 px-3">Vigência</th>
                          <th className="py-2.5 px-3 text-right">Ação</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/60">
                        {selectedOp.rules.map((rule) => (
                          <tr key={rule.id} className="hover:bg-muted/20 transition-colors">
                            <td className="py-2.5 px-3 font-mono font-bold text-foreground">{rule.priority}</td>
                            <td className="py-2.5 px-3 font-medium text-foreground">{rule.description}</td>
                            <td className="py-2.5 px-3">
                              <Badge variant="default" className="font-mono text-xs bg-primary/20 text-primary border-primary/30">
                                {rule.cfop}
                              </Badge>
                            </td>
                            <td className="py-2.5 px-3 space-y-0.5 text-[11px]">
                              <div>
                                {rule.is_same_uf === true ? (
                                  <span className="text-emerald-400">Mesma UF</span>
                                ) : rule.is_same_uf === false ? (
                                  <span className="text-amber-400">Outras UFs</span>
                                ) : (
                                  <span className="text-muted-foreground">Qualquer UF</span>
                                )}
                              </div>
                              {rule.is_final_consumer !== null && (
                                <div className="text-[10px] text-muted-foreground">
                                  {rule.is_final_consumer ? "Consumidor Final" : "Revenda/Industrialização"}
                                </div>
                              )}
                            </td>
                            <td className="py-2.5 px-3 text-[11px] font-mono text-muted-foreground">
                              {rule.effective_from} até {rule.effective_to || "Indeterminado"}
                            </td>
                            <td className="py-2.5 px-3 text-right">
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-7 w-7 text-rose-400 hover:text-rose-300 hover:bg-rose-500/10"
                                onClick={() => handleDeleteRule(rule.id)}
                                title="Remover Regra"
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
              </div>
            </Card>
          ) : (
            <div className="p-12 text-center text-muted-foreground text-xs">
              Selecione uma operação fiscal ao lado.
            </div>
          )}

          {/* Simulator Card */}
          <Card className="border-border/60 shadow-sm space-y-4 p-5 bg-muted/20">
            <div className="flex items-center justify-between pb-2 border-b border-border/40">
              <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
                <Play className="h-4 w-4 text-emerald-400" /> Simulador de Cenário Fiscal & Matching de CFOP
              </h3>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div>
                <label className="text-[11px] text-muted-foreground block mb-1">UF Origem</label>
                <Input value={simUfOrigin} onChange={(e) => setSimUfOrigin(e.target.value)} className="h-8 text-xs font-mono" />
              </div>
              <div>
                <label className="text-[11px] text-muted-foreground block mb-1">UF Destino</label>
                <Input value={simUfDest} onChange={(e) => setSimUfDest(e.target.value)} className="h-8 text-xs font-mono" />
              </div>
              <div>
                <label className="text-[11px] text-muted-foreground block mb-1">Modelo DF-e</label>
                <select
                  value={simDocModel}
                  onChange={(e) => setSimDocModel(e.target.value)}
                  className="w-full h-8 rounded-md bg-card border border-border px-2 text-xs"
                >
                  <option value="55">NF-e (55)</option>
                  <option value="65">NFC-e (65)</option>
                </select>
              </div>
              <div>
                <label className="text-[11px] text-muted-foreground block mb-1">Operação</label>
                <select
                  value={simOpCode}
                  onChange={(e) => setSimOpCode(e.target.value)}
                  className="w-full h-8 rounded-md bg-card border border-border px-2 text-xs"
                >
                  {operations.map((op) => (
                    <option key={op.id} value={op.code}>
                      {op.name} ({op.code})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex items-center gap-4 text-xs">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={simFinalConsumer}
                  onChange={(e) => setSimFinalConsumer(e.target.checked)}
                  className="rounded border-border"
                />
                Destinatário é Consumidor Final
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={simTaxContrib}
                  onChange={(e) => setSimTaxContrib(e.target.checked)}
                  className="rounded border-border"
                />
                Destinatário é Contribuinte ICMS
              </label>

              <Button
                onClick={handleRunSimulator}
                disabled={simulating}
                size="sm"
                className="ml-auto gap-1.5 text-xs bg-emerald-600 hover:bg-emerald-500 text-white"
              >
                <Play className="h-3.5 w-3.5" /> Testar Resolução
              </Button>
            </div>

            {simResult && (
              <div
                className={`p-4 rounded-xl border text-xs space-y-2 ${
                  simResult.matched
                    ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                    : "bg-rose-500/10 border-rose-500/30 text-rose-300"
                }`}
              >
                <div className="font-bold flex items-center justify-between">
                  <span>{simResult.matched ? "CFOP Resolvido com Sucesso!" : "Falha na Resolução"}</span>
                  {simResult.cfop && <Badge className="text-sm font-mono">{simResult.cfop}</Badge>}
                </div>
                <p className="text-[11px] opacity-90">{simResult.reason}</p>
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Modal simples para criação de regra */}
      {isRuleModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border/80 rounded-2xl w-full max-w-md p-6 space-y-4 shadow-xl">
            <h3 className="text-base font-bold">Nova Regra de Cenário CFOP</h3>

            <form onSubmit={handleAddRule} className="space-y-3 text-xs">
              <div>
                <label className="block mb-1 font-semibold">Descrição da Regra *</label>
                <Input
                  required
                  placeholder="ex: Venda Interestadual Consumidor Final"
                  value={ruleDescription}
                  onChange={(e) => setRuleDescription(e.target.value)}
                  className="text-xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block mb-1 font-semibold">CFOP Resultante *</label>
                  <Input
                    required
                    maxLength={4}
                    placeholder="ex: 6108"
                    value={ruleCfop}
                    onChange={(e) => setRuleCfop(e.target.value)}
                    className="font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="block mb-1 font-semibold">Prioridade (1-100)</label>
                  <Input
                    type="number"
                    value={rulePriority}
                    onChange={(e) => setRulePriority(Number(e.target.value))}
                    className="text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block mb-1 text-muted-foreground">Mesma UF?</label>
                  <select
                    value={ruleIsSameUf}
                    onChange={(e) => setRuleIsSameUf(e.target.value)}
                    className="w-full h-9 rounded-md bg-muted/50 border border-border px-2 text-xs"
                  >
                    <option value="any">Qualquer UF</option>
                    <option value="yes">Mesma UF (Interna)</option>
                    <option value="no">Outras UFs (Interestadual)</option>
                  </select>
                </div>

                <div>
                  <label className="block mb-1 text-muted-foreground">Consumidor Final?</label>
                  <select
                    value={ruleIsFinalConsumer}
                    onChange={(e) => setRuleIsFinalConsumer(e.target.value)}
                    className="w-full h-9 rounded-md bg-muted/50 border border-border px-2 text-xs"
                  >
                    <option value="any">Qualquer</option>
                    <option value="yes">Sim (Consumidor Final)</option>
                    <option value="no">Não (Revenda/Industr.)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block mb-1 text-muted-foreground">Início Vigência *</label>
                  <Input
                    type="date"
                    required
                    value={ruleEffectiveFrom}
                    onChange={(e) => setRuleEffectiveFrom(e.target.value)}
                    className="text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="block mb-1 text-muted-foreground">Fim Vigência</label>
                  <Input
                    type="date"
                    value={ruleEffectiveTo}
                    onChange={(e) => setRuleEffectiveTo(e.target.value)}
                    className="text-xs font-mono"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-border/40">
                <Button variant="ghost" type="button" onClick={() => setIsRuleModalOpen(false)}>
                  Cancelar
                </Button>
                <Button type="submit">Salvar Regra</Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
