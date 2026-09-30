import { useState, useEffect } from "react";
import {
  FileText,
  Save,
  X,
  AlertCircle,
  Layers,
  Scale,
  Calendar,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ProductFiscalProfileInput } from "@/types/product_fiscal";
import { productFiscalService } from "@/services/productFiscalService";
import { useAuthStore } from "@/store/useAuthStore";

interface ProductFiscalModalProps {
  isOpen: boolean;
  onClose: () => void;
  productId: string;
  productName: string;
  onSuccess?: () => void;
}

export function ProductFiscalModal({
  isOpen,
  onClose,
  productId,
  productName,
  onSuccess,
}: ProductFiscalModalProps) {
  const { activeCompany } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [activeTab, setActiveTab] = useState<"geral" | "icms" | "outros" | "rtc">("geral");

  const [formData, setFormData] = useState<ProductFiscalProfileInput>({
    ncm: "",
    cest: "",
    origin: 0,
    gtin_commercial: "",
    gtin_taxable: "",
    unit_commercial: "UN",
    unit_taxable: "UN",
    conversion_factor: 1.0,
    cst_csosn: "102",
    cfop_default_inside: "5102",
    cfop_default_outside: "6102",
    icms_rate: 0.0,
    icms_st_rate: 0.0,
    fcp_rate: 0.0,
    ipi_cst: "99",
    ipi_rate: 0.0,
    pis_cst: "49",
    pis_rate: 0.0,
    cofins_cst: "49",
    cofins_rate: 0.0,
    ibs_cst: "01",
    ibs_rate: 0.0,
    cbs_cst: "01",
    cbs_rate: 0.0,
    source_reference: "",
  });

  const [profileMeta, setProfileMeta] = useState<{
    effective_from?: string;
    created_at?: string;
  } | null>(null);

  useEffect(() => {
    if (!isOpen || !productId || !activeCompany) return;

    setLoading(true);
    setErrorMessage("");
    productFiscalService
      .getFiscalProfile(productId, activeCompany.id)
      .then((profile) => {
        if (profile) {
          setFormData({
            ncm: profile.ncm || "",
            cest: profile.cest || "",
            origin: profile.origin ?? 0,
            gtin_commercial: profile.gtin_commercial || "",
            gtin_taxable: profile.gtin_taxable || "",
            unit_commercial: profile.unit_commercial || "UN",
            unit_taxable: profile.unit_taxable || "UN",
            conversion_factor: profile.conversion_factor ?? 1.0,
            cst_csosn: profile.cst_csosn || "102",
            cfop_default_inside: profile.cfop_default_inside || "5102",
            cfop_default_outside: profile.cfop_default_outside || "6102",
            icms_rate: profile.icms_rate ?? 0.0,
            icms_st_rate: profile.icms_st_rate ?? 0.0,
            fcp_rate: profile.fcp_rate ?? 0.0,
            ipi_cst: profile.ipi_cst || "99",
            ipi_rate: profile.ipi_rate ?? 0.0,
            pis_cst: profile.pis_cst || "49",
            pis_rate: profile.pis_rate ?? 0.0,
            cofins_cst: profile.cofins_cst || "49",
            cofins_rate: profile.cofins_rate ?? 0.0,
            ibs_cst: profile.ibs_cst || "01",
            ibs_rate: profile.ibs_rate ?? 0.0,
            cbs_cst: profile.cbs_cst || "01",
            cbs_rate: profile.cbs_rate ?? 0.0,
            source_reference: profile.source_reference || "",
          });
          setProfileMeta({
            effective_from: profile.effective_from,
            created_at: profile.created_at,
          });
        } else {
          setProfileMeta(null);
        }
      })
      .catch((err) => {
        console.error("Erro ao carregar perfil fiscal:", err);
      })
      .finally(() => setLoading(false));
  }, [isOpen, productId, activeCompany]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCompany) return;

    setSaving(true);
    setErrorMessage("");
    try {
      await productFiscalService.updateFiscalProfile(productId, formData, activeCompany.id);
      if (onSuccess) onSuccess();
      onClose();
    } catch (err: any) {
      setErrorMessage(err?.message || "Erro ao salvar perfil fiscal do produto.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-xl shadow-2xl w-full max-w-3xl overflow-hidden flex flex-col max-h-[90vh] animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-4 border-b border-border bg-muted/40 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-9 w-9 rounded-lg bg-primary/10 text-primary flex items-center justify-center font-bold">
              <FileText className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-foreground">Perfil Fiscal & Tributação</h2>
              <p className="text-xs text-muted-foreground truncate max-w-md">
                Produto: <strong className="text-foreground font-semibold">{productName}</strong>
              </p>
            </div>
          </div>

          <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8 text-muted-foreground hover:text-foreground">
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Sub-tabs */}
        <div className="px-4 pt-3 border-b border-border flex items-center gap-2 bg-card">
          <button
            onClick={() => setActiveTab("geral")}
            className={`px-3 py-2 text-xs font-semibold border-b-2 transition-colors ${
              activeTab === "geral"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            1. Dados Gerais (NCM/Origem/GTIN)
          </button>
          <button
            onClick={() => setActiveTab("icms")}
            className={`px-3 py-2 text-xs font-semibold border-b-2 transition-colors ${
              activeTab === "icms"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            2. ICMS, ST & CFOP
          </button>
          <button
            onClick={() => setActiveTab("outros")}
            className={`px-3 py-2 text-xs font-semibold border-b-2 transition-colors ${
              activeTab === "outros"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            3. IPI, PIS & COFINS
          </button>
          <button
            onClick={() => setActiveTab("rtc")}
            className={`px-3 py-2 text-xs font-semibold border-b-2 transition-colors flex items-center gap-1 ${
              activeTab === "rtc"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Scale className="h-3.5 w-3.5 text-blue-500" /> 4. Reforma Tributária (IBS/CBS)
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-4">
          {errorMessage && (
            <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-xs flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {loading ? (
            <div className="py-12 text-center text-xs text-muted-foreground">
              Carregando perfil fiscal...
            </div>
          ) : (
            <>
              {/* TAB 1: DADOS GERAIS */}
              {activeTab === "geral" && (
                <div className="space-y-4 text-xs">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div>
                      <label className="font-semibold block mb-1">NCM (8 dígitos) *</label>
                      <Input
                        placeholder="Ex: 22021000"
                        maxLength={8}
                        value={formData.ncm || ""}
                        onChange={(e) => setFormData({ ...formData, ncm: e.target.value })}
                        className="h-9 font-mono text-xs"
                      />
                    </div>

                    <div>
                      <label className="font-semibold block mb-1">CEST (7 dígitos)</label>
                      <Input
                        placeholder="Ex: 0301000 (se ST)"
                        maxLength={7}
                        value={formData.cest || ""}
                        onChange={(e) => setFormData({ ...formData, cest: e.target.value })}
                        className="h-9 font-mono text-xs"
                      />
                    </div>

                    <div>
                      <label className="font-semibold block mb-1">Origem da Mercadoria *</label>
                      <select
                        value={formData.origin}
                        onChange={(e) => setFormData({ ...formData, origin: parseInt(e.target.value) })}
                        className="w-full h-9 rounded-md border border-input bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                      >
                        <option value={0}>0 - Nacional</option>
                        <option value={1}>1 - Estrangeira (Importação Direta)</option>
                        <option value={2}>2 - Estrangeira (Adquirida no Mercado Interno)</option>
                        <option value={3}>3 - Nacional (Conteúdo Importação &gt; 40%)</option>
                        <option value={4}>4 - Nacional (Processos Produtivos Básicos)</option>
                        <option value={5}>5 - Nacional (Conteúdo Importação &lt;= 40%)</option>
                        <option value={6}>6 - Estrangeira (Sem Similar Nacional - CAMEX)</option>
                        <option value={7}>7 - Estrangeira (Mercado Interno sem Similar)</option>
                        <option value={8}>8 - Nacional (Importação Conteúdo Superior a 70%)</option>
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                    <div>
                      <label className="font-semibold block mb-1">GTIN / EAN Comercial</label>
                      <Input
                        placeholder="Ex: 7894900011517 ou 'SEM GTIN'"
                        value={formData.gtin_commercial || ""}
                        onChange={(e) => setFormData({ ...formData, gtin_commercial: e.target.value })}
                        className="h-9 text-xs"
                      />
                    </div>

                    <div>
                      <label className="font-semibold block mb-1">GTIN / EAN Tributável</label>
                      <Input
                        placeholder="Ex: 7894900011517 ou 'SEM GTIN'"
                        value={formData.gtin_taxable || ""}
                        onChange={(e) => setFormData({ ...formData, gtin_taxable: e.target.value })}
                        className="h-9 text-xs"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
                    <div>
                      <label className="font-semibold block mb-1">Unidade Comercial</label>
                      <Input
                        placeholder="Ex: UN, CX, KG"
                        value={formData.unit_commercial || "UN"}
                        onChange={(e) => setFormData({ ...formData, unit_commercial: e.target.value })}
                        className="h-9 text-xs"
                      />
                    </div>

                    <div>
                      <label className="font-semibold block mb-1">Unidade Tributável</label>
                      <Input
                        placeholder="Ex: UN, KG"
                        value={formData.unit_taxable || "UN"}
                        onChange={(e) => setFormData({ ...formData, unit_taxable: e.target.value })}
                        className="h-9 text-xs"
                      />
                    </div>

                    <div>
                      <label className="font-semibold block mb-1">Fator de Conversão</label>
                      <Input
                        type="number"
                        step="0.0001"
                        value={formData.conversion_factor}
                        onChange={(e) => setFormData({ ...formData, conversion_factor: parseFloat(e.target.value) || 1.0 })}
                        className="h-9 text-xs font-mono"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: ICMS & CFOP */}
              {activeTab === "icms" && (
                <div className="space-y-4 text-xs">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div>
                      <label className="font-semibold block mb-1">CSOSN / CST (ICMS) *</label>
                      <select
                        value={formData.cst_csosn || "102"}
                        onChange={(e) => setFormData({ ...formData, cst_csosn: e.target.value })}
                        className="w-full h-9 rounded-md border border-input bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                      >
                        <optgroup label="Simples Nacional (CSOSN)">
                          <option value="101">101 - Tributada com permissão de crédito</option>
                          <option value="102">102 - Tributada sem permissão de crédito</option>
                          <option value="103">103 - Isenção do ICMS para faixa de receita</option>
                          <option value="201">201 - Com permissão de crédito e ST</option>
                          <option value="202">202 - Sem permissão de crédito e com ST</option>
                          <option value="500">500 - ICMS cobrado antes por ST / antecipado</option>
                          <option value="900">900 - Outros</option>
                        </optgroup>
                        <optgroup label="Regime Normal (CST)">
                          <option value="00">00 - Tributada integralmente</option>
                          <option value="10">10 - Tributada e com cobrança por ST</option>
                          <option value="20">20 - Com redução de base de cálculo</option>
                          <option value="40">40 - Isenta</option>
                          <option value="41">41 - Não tributada</option>
                          <option value="60">60 - ICMS cobrado anteriormente por ST</option>
                          <option value="90">90 - Outras</option>
                        </optgroup>
                      </select>
                    </div>

                    <div>
                      <label className="font-semibold block mb-1">CFOP Padrão Estadual (Interno) *</label>
                      <Input
                        placeholder="Ex: 5102"
                        maxLength={4}
                        value={formData.cfop_default_inside}
                        onChange={(e) => setFormData({ ...formData, cfop_default_inside: e.target.value })}
                        className="h-9 font-mono text-xs"
                      />
                    </div>

                    <div>
                      <label className="font-semibold block mb-1">CFOP Interestadual (Fora do Estado) *</label>
                      <Input
                        placeholder="Ex: 6102"
                        maxLength={4}
                        value={formData.cfop_default_outside}
                        onChange={(e) => setFormData({ ...formData, cfop_default_outside: e.target.value })}
                        className="h-9 font-mono text-xs"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
                    <div>
                      <label className="font-semibold block mb-1">Alíquota ICMS própria (%)</label>
                      <Input
                        type="number"
                        step="0.01"
                        value={formData.icms_rate}
                        onChange={(e) => setFormData({ ...formData, icms_rate: parseFloat(e.target.value) || 0.0 })}
                        className="h-9 font-mono text-xs"
                      />
                    </div>

                    <div>
                      <label className="font-semibold block mb-1">Alíquota ICMS ST (%)</label>
                      <Input
                        type="number"
                        step="0.01"
                        value={formData.icms_st_rate}
                        onChange={(e) => setFormData({ ...formData, icms_st_rate: parseFloat(e.target.value) || 0.0 })}
                        className="h-9 font-mono text-xs"
                      />
                    </div>

                    <div>
                      <label className="font-semibold block mb-1">Alíquota FCP (%)</label>
                      <Input
                        type="number"
                        step="0.01"
                        value={formData.fcp_rate}
                        onChange={(e) => setFormData({ ...formData, fcp_rate: parseFloat(e.target.value) || 0.0 })}
                        className="h-9 font-mono text-xs"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 3: IPI, PIS, COFINS */}
              {activeTab === "outros" && (
                <div className="space-y-4 text-xs">
                  {/* IPI */}
                  <div className="p-3 rounded-lg border border-border bg-muted/20 space-y-2">
                    <h3 className="font-bold text-foreground flex items-center gap-1.5">
                      <Layers className="h-4 w-4 text-amber-500" /> IPI (Imposto sobre Produtos Industrializados)
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div>
                        <label className="font-semibold block mb-1">CST IPI</label>
                        <Input
                          placeholder="Ex: 50, 53, 99"
                          maxLength={3}
                          value={formData.ipi_cst || "99"}
                          onChange={(e) => setFormData({ ...formData, ipi_cst: e.target.value })}
                          className="h-9 font-mono text-xs"
                        />
                      </div>
                      <div>
                        <label className="font-semibold block mb-1">Alíquota IPI (%)</label>
                        <Input
                          type="number"
                          step="0.01"
                          value={formData.ipi_rate}
                          onChange={(e) => setFormData({ ...formData, ipi_rate: parseFloat(e.target.value) || 0.0 })}
                          className="h-9 font-mono text-xs"
                        />
                      </div>
                    </div>
                  </div>

                  {/* PIS & COFINS */}
                  <div className="p-3 rounded-lg border border-border bg-muted/20 space-y-2">
                    <h3 className="font-bold text-foreground flex items-center gap-1.5">
                      <Layers className="h-4 w-4 text-emerald-500" /> PIS & COFINS
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                      <div>
                        <label className="font-semibold block mb-1">CST PIS</label>
                        <Input
                          placeholder="Ex: 01, 07, 49"
                          maxLength={2}
                          value={formData.pis_cst || "49"}
                          onChange={(e) => setFormData({ ...formData, pis_cst: e.target.value })}
                          className="h-9 font-mono text-xs"
                        />
                      </div>
                      <div>
                        <label className="font-semibold block mb-1">Alíquota PIS (%)</label>
                        <Input
                          type="number"
                          step="0.01"
                          value={formData.pis_rate}
                          onChange={(e) => setFormData({ ...formData, pis_rate: parseFloat(e.target.value) || 0.0 })}
                          className="h-9 font-mono text-xs"
                        />
                      </div>
                      <div>
                        <label className="font-semibold block mb-1">CST COFINS</label>
                        <Input
                          placeholder="Ex: 01, 07, 49"
                          maxLength={2}
                          value={formData.cofins_cst || "49"}
                          onChange={(e) => setFormData({ ...formData, cofins_cst: e.target.value })}
                          className="h-9 font-mono text-xs"
                        />
                      </div>
                      <div>
                        <label className="font-semibold block mb-1">Alíquota COFINS (%)</label>
                        <Input
                          type="number"
                          step="0.01"
                          value={formData.cofins_rate}
                          onChange={(e) => setFormData({ ...formData, cofins_rate: parseFloat(e.target.value) || 0.0 })}
                          className="h-9 font-mono text-xs"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 4: REFORMA TRIBUTÁRIA RTC (IBS / CBS) */}
              {activeTab === "rtc" && (
                <div className="space-y-4 text-xs">
                  <div className="p-3.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-600 dark:text-blue-300 space-y-1">
                    <h3 className="font-bold flex items-center gap-1.5 text-sm">
                      <Scale className="h-4 w-4 text-blue-500" /> Estrutura Nativa RTC (IBS / CBS)
                    </h3>
                    <p className="text-[11px] leading-relaxed">
                      Campos preparados para a transição da Reforma Tributária (RTC 2026/2027). A tributação atual (ICMS/PIS/COFINS) é preservada e os grupos IBS/CBS são versionados paralelamente.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* IBS */}
                    <div className="p-3 rounded-lg border border-border bg-card space-y-2">
                      <h4 className="font-bold text-foreground">IBS (Imposto sobre Bens e Serviços)</h4>
                      <div>
                        <label className="font-semibold block mb-1">CST IBS</label>
                        <Input
                          placeholder="Ex: 01"
                          maxLength={3}
                          value={formData.ibs_cst || "01"}
                          onChange={(e) => setFormData({ ...formData, ibs_cst: e.target.value })}
                          className="h-9 font-mono text-xs"
                        />
                      </div>
                      <div>
                        <label className="font-semibold block mb-1">Alíquota Teste IBS (%)</label>
                        <Input
                          type="number"
                          step="0.01"
                          value={formData.ibs_rate}
                          onChange={(e) => setFormData({ ...formData, ibs_rate: parseFloat(e.target.value) || 0.0 })}
                          className="h-9 font-mono text-xs"
                        />
                      </div>
                    </div>

                    {/* CBS */}
                    <div className="p-3 rounded-lg border border-border bg-card space-y-2">
                      <h4 className="font-bold text-foreground">CBS (Contribuição sobre Bens e Serviços)</h4>
                      <div>
                        <label className="font-semibold block mb-1">CST CBS</label>
                        <Input
                          placeholder="Ex: 01"
                          maxLength={3}
                          value={formData.cbs_cst || "01"}
                          onChange={(e) => setFormData({ ...formData, cbs_cst: e.target.value })}
                          className="h-9 font-mono text-xs"
                        />
                      </div>
                      <div>
                        <label className="font-semibold block mb-1">Alíquota Teste CBS (%)</label>
                        <Input
                          type="number"
                          step="0.01"
                          value={formData.cbs_rate}
                          onChange={(e) => setFormData({ ...formData, cbs_rate: parseFloat(e.target.value) || 0.0 })}
                          className="h-9 font-mono text-xs"
                        />
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="font-semibold block mb-1">Origem Legal / Referência Normativa</label>
                    <Input
                      placeholder="Ex: Tabela SEFAZ SP Resolução X/2026, Orientação Contábil..."
                      value={formData.source_reference || ""}
                      onChange={(e) => setFormData({ ...formData, source_reference: e.target.value })}
                      className="h-9 text-xs"
                    />
                  </div>
                </div>
              )}

              {/* Metadata de Vigência se existir */}
              {profileMeta?.effective_from && (
                <div className="p-3 rounded-lg bg-muted/40 border border-border text-[11px] text-muted-foreground flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Calendar className="h-3.5 w-3.5 text-primary" /> Vigência desta versão:{" "}
                    <strong className="text-foreground font-mono">
                      {new Date(profileMeta.effective_from).toLocaleString("pt-BR")}
                    </strong>
                  </span>
                  <Badge variant="outline" className="text-[10px]">
                    Versionamento Histórico Ativo
                  </Badge>
                </div>
              )}
            </>
          )}

          {/* Footer Actions */}
          <div className="pt-4 border-t border-border flex items-center justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose} disabled={saving} className="h-9 text-xs">
              Cancelar
            </Button>
            <Button type="submit" disabled={saving || loading} className="h-9 text-xs bg-primary gap-1.5 font-semibold">
              <Save className="h-4 w-4" />
              {saving ? "Salvando Versão..." : "Salvar Perfil Fiscal"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
