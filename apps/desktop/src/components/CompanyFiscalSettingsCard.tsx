import { useState, useEffect } from "react";
import {
  Building2,
  Key,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Upload,
  RefreshCw,
  Plus,
  Save,
  Layers,
  FileCheck,
  WifiOff,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  CompanyFiscalConfigInput,
  FiscalSeries,
  FiscalSeriesInput,
  FiscalCertificateMetadata,
} from "@/types/company_fiscal";
import { companyFiscalService } from "@/services/companyFiscalService";
import { useAuthStore } from "@/store/useAuthStore";

export function CompanyFiscalSettingsCard() {
  const { activeCompany } = useAuthStore();

  const [loading, setLoading] = useState(true);
  const [savingConfig, setSavingConfig] = useState(false);
  const [uploadingCert, setUploadingCert] = useState(false);
  const [savingSeries, setSavingSeries] = useState(false);

  const [feedbackMsg, setFeedbackMsg] = useState<{ type: "success" | "error"; msg: string } | null>(null);

  const [config, setConfig] = useState<CompanyFiscalConfigInput>({
    environment: "HOMOLOGATION",
    tax_regime: "SIMPLES_NACIONAL",
    crt: 1,
    state_tax_number: "",
    municipal_tax_number: "",
    ibge_city_code: "",
    nfc_csc_id: "",
    nfc_csc_secret: "",
    nfse_provider: "NACIONAL",
    nfse_environment: "HOMOLOGATION",
    contingency_mode: "NONE",
    contingency_reason: "",
  });

  const [certMeta, setCertMeta] = useState<FiscalCertificateMetadata | null>(null);
  const [seriesList, setSeriesList] = useState<FiscalSeries[]>([]);

  // Cert Upload State
  const [certFile, setCertFile] = useState<File | null>(null);
  const [certPassword, setCertPassword] = useState("");

  // New Series State
  const [isSeriesModalOpen, setIsSeriesModalOpen] = useState(false);
  const [newSeriesData, setNewSeriesData] = useState<FiscalSeriesInput>({
    doc_model: "55",
    series: 1,
    current_number: 0,
    environment: "HOMOLOGATION",
    is_active: true,
  });

  const loadAllFiscalData = async () => {
    if (!activeCompany) return;
    setLoading(true);
    try {
      const [cfg, cert, sList] = await Promise.all([
        companyFiscalService.getFiscalConfig(activeCompany.id),
        companyFiscalService.getCertificateMetadata(activeCompany.id),
        companyFiscalService.getFiscalSeries(activeCompany.id),
      ]);

      setConfig({
        environment: cfg.environment,
        tax_regime: cfg.tax_regime,
        crt: cfg.crt,
        state_tax_number: cfg.state_tax_number || "",
        municipal_tax_number: cfg.municipal_tax_number || "",
        ibge_city_code: cfg.ibge_city_code || "",
        nfc_csc_id: cfg.nfc_csc_id || "",
        nfc_csc_secret: "", // Oculto por segurança
        nfse_provider: cfg.nfse_provider || "NACIONAL",
        nfse_environment: cfg.nfse_environment || "HOMOLOGATION",
        contingency_mode: cfg.contingency_mode || "NONE",
        contingency_reason: cfg.contingency_reason || "",
      });

      setCertMeta(cert);
      setSeriesList(sList);
    } catch (err) {
      console.error("Erro ao carregar dados fiscais da empresa:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllFiscalData();
  }, [activeCompany]);

  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCompany) return;

    setSavingConfig(true);
    setFeedbackMsg(null);
    try {
      await companyFiscalService.updateFiscalConfig(config, activeCompany.id);
      setFeedbackMsg({ type: "success", msg: "Parâmetros fiscais salvos com sucesso!" });
      loadAllFiscalData();
    } catch (err: any) {
      setFeedbackMsg({ type: "error", msg: err?.message || "Erro ao salvar parâmetros fiscais." });
    } finally {
      setSavingConfig(false);
    }
  };

  const handleUploadCert = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCompany || !certFile || !certPassword) return;

    setUploadingCert(true);
    setFeedbackMsg(null);
    try {
      const updatedMeta = await companyFiscalService.uploadCertificate(certFile, certPassword, activeCompany.id);
      setCertMeta(updatedMeta);
      setCertFile(null);
      setCertPassword("");
      setFeedbackMsg({ type: "success", msg: "Certificado A1 validado e armazenado com sucesso!" });
    } catch (err: any) {
      setFeedbackMsg({ type: "error", msg: err?.message || "Erro ao importar certificado A1." });
    } finally {
      setUploadingCert(false);
    }
  };

  const handleSaveSeries = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCompany) return;

    setSavingSeries(true);
    setFeedbackMsg(null);
    try {
      await companyFiscalService.upsertFiscalSeries(newSeriesData, activeCompany.id);
      setIsSeriesModalOpen(false);
      setFeedbackMsg({ type: "success", msg: "Série fiscal cadastrada com sucesso!" });
      loadAllFiscalData();
    } catch (err: any) {
      setFeedbackMsg({ type: "error", msg: err?.message || "Erro ao salvar série fiscal." });
    } finally {
      setSavingSeries(false);
    }
  };

  if (loading) {
    return (
      <Card className="border-border/60">
        <CardContent className="p-12 text-center text-xs text-muted-foreground flex flex-col items-center justify-center space-y-2">
          <RefreshCw className="h-6 w-6 animate-spin text-primary" />
          <span>Carregando parâmetros fiscais da empresa...</span>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {feedbackMsg && (
        <div
          className={`p-3 rounded-lg text-xs flex items-center gap-2 ${
            feedbackMsg.type === "success"
              ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400"
              : "bg-destructive/10 border border-destructive/20 text-destructive"
          }`}
        >
          {feedbackMsg.type === "success" ? (
            <CheckCircle2 className="h-4 w-4 shrink-0" />
          ) : (
            <AlertTriangle className="h-4 w-4 shrink-0" />
          )}
          <span>{feedbackMsg.msg}</span>
        </div>
      )}

      {/* 1. CONFIGURAÇÃO FISCAL E AMBIENTE */}
      <Card className="border-border/60 shadow-sm">
        <CardHeader className="pb-3 border-b border-border/60">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-blue-500/10 text-blue-500 flex items-center justify-center font-bold">
                <Building2 className="h-4 w-4" />
              </div>
              <div>
                <CardTitle className="text-base font-bold">Configuração Tributária & Ambiente</CardTitle>
                <CardDescription className="text-xs">
                  CRT, Inscrições e ambiente oficial de emissão de NF-e, NFC-e e NFS-e.
                </CardDescription>
              </div>
            </div>

            <Badge
              variant={config.environment === "PRODUCTION" ? "destructive" : "outline"}
              className={config.environment === "HOMOLOGATION" ? "border-amber-500/40 text-amber-500 bg-amber-500/10" : ""}
            >
              {config.environment === "PRODUCTION" ? "Produção SEFAZ" : "Homologação / Testes"}
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="p-6">
          <form onSubmit={handleSaveConfig} className="space-y-4 text-xs">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="font-semibold block mb-1">Ambiente SEFAZ *</label>
                <select
                  value={config.environment}
                  onChange={(e) => setConfig({ ...config, environment: e.target.value as any })}
                  className="w-full h-9 rounded-md border border-input bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary font-semibold"
                >
                  <option value="HOMOLOGATION">Homologação (Sem Valor Fiscal / Testes)</option>
                  <option value="PRODUCTION">Produção (Emissão Real SEFAZ)</option>
                </select>
              </div>

              <div>
                <label className="font-semibold block mb-1">Regime Tributário / CRT *</label>
                <select
                  value={config.crt}
                  onChange={(e) => setConfig({ ...config, crt: parseInt(e.target.value) })}
                  className="w-full h-9 rounded-md border border-input bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value={1}>1 - Simples Nacional</option>
                  <option value={2}>2 - Simples Nacional (Excesso de Sublimite)</option>
                  <option value={3}>3 - Regime Normal (Lucro Presumido / Real)</option>
                  <option value={4}>4 - MEI (Microempreendedor Individual)</option>
                </select>
              </div>

              <div>
                <label className="font-semibold block mb-1">Código IBGE do Município *</label>
                <Input
                  placeholder="Ex: 3550308 (São Paulo)"
                  maxLength={7}
                  value={config.ibge_city_code || ""}
                  onChange={(e) => setConfig({ ...config, ibge_city_code: e.target.value })}
                  className="h-9 font-mono text-xs"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div>
                <label className="font-semibold block mb-1">Inscrição Estadual (IE)</label>
                <Input
                  placeholder="Ex: 123456789 ou 'ISENTO'"
                  value={config.state_tax_number || ""}
                  onChange={(e) => setConfig({ ...config, state_tax_number: e.target.value })}
                  className="h-9 text-xs"
                />
              </div>

              <div>
                <label className="font-semibold block mb-1">Inscrição Municipal (IM)</label>
                <Input
                  placeholder="Ex: 987654"
                  value={config.municipal_tax_number || ""}
                  onChange={(e) => setConfig({ ...config, municipal_tax_number: e.target.value })}
                  className="h-9 text-xs"
                />
              </div>
            </div>

            {/* Token CSC NFC-e */}
            <div className="p-3.5 rounded-lg border border-border bg-muted/20 space-y-3 pt-3">
              <h3 className="font-bold text-foreground flex items-center gap-1.5">
                <Key className="h-4 w-4 text-emerald-500" /> Token CSC (Código de Segurança do Contribuinte - NFC-e)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold block mb-1">CSC ID / Token ID (ex: 000001)</label>
                  <Input
                    placeholder="Ex: 000001"
                    value={config.nfc_csc_id || ""}
                    onChange={(e) => setConfig({ ...config, nfc_csc_id: e.target.value })}
                    className="h-9 text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="font-semibold block mb-1">CSC Secret (Segredo Criptografado)</label>
                  <Input
                    type="password"
                    placeholder="Atualizar código segredo do CSC..."
                    value={config.nfc_csc_secret || ""}
                    onChange={(e) => setConfig({ ...config, nfc_csc_secret: e.target.value })}
                    className="h-9 text-xs font-mono"
                  />
                </div>
              </div>
            </div>

            {/* Modo de Contingência */}
            <div className="p-3.5 rounded-lg border border-border bg-muted/20 space-y-3">
              <h3 className="font-bold text-foreground flex items-center gap-1.5">
                <WifiOff className="h-4 w-4 text-amber-500" /> Modo de Contingência Fiscal
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold block mb-1">Status de Contingência</label>
                  <select
                    value={config.contingency_mode}
                    onChange={(e) => setConfig({ ...config, contingency_mode: e.target.value as any })}
                    className="w-full h-9 rounded-md border border-input bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary font-semibold"
                  >
                    <option value="NONE">Operação Normal (Online SEFAZ)</option>
                    <option value="OFFLINE_NFC">Contingência Offline NFC-e (Fila Local)</option>
                    <option value="EPEC">Contingência EPEC (NF-e Modelo 55)</option>
                  </select>
                </div>
                <div>
                  <label className="font-semibold block mb-1">Justificativa Legal de Entrada em Contingência</label>
                  <Input
                    placeholder="Ex: Indisponibilidade de conexão SEFAZ Estadual..."
                    value={config.contingency_reason || ""}
                    onChange={(e) => setConfig({ ...config, contingency_reason: e.target.value })}
                    className="h-9 text-xs"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <Button type="submit" disabled={savingConfig} className="h-9 text-xs bg-primary gap-1.5 font-semibold">
                <Save className="h-4 w-4" /> {savingConfig ? "Salvando..." : "Salvar Configurações Fiscais"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* 2. CERTIFICADO DIGITAL A1 */}
      <Card className="border-border/60 shadow-sm">
        <CardHeader className="pb-3 border-b border-border/60">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-emerald-500/10 text-emerald-500 flex items-center justify-center font-bold">
                <ShieldCheck className="h-4 w-4" />
              </div>
              <div>
                <CardTitle className="text-base font-bold">Certificado Digital A1</CardTitle>
                <CardDescription className="text-xs">
                  Armazenamento simétrico encriptado (Fernet/AES-256) do arquivo .pfx/.p12.
                </CardDescription>
              </div>
            </div>

            {certMeta ? (
              <Badge variant={certMeta.is_valid ? "success" : "destructive"}>
                {certMeta.is_valid ? "Certificado Válido" : "Certificado Expirado"}
              </Badge>
            ) : (
              <Badge variant="outline" className="text-amber-500 border-amber-500/30 bg-amber-500/10">
                Pendente de Upload
              </Badge>
            )}
          </div>
        </CardHeader>

        <CardContent className="p-6 space-y-6 text-xs">
          {/* Active Certificate Info */}
          {certMeta ? (
            <div className="p-4 rounded-xl bg-card border border-border space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border pb-3">
                <div>
                  <span className="text-[10px] text-muted-foreground uppercase font-semibold tracking-wider">Titular / CNPJ</span>
                  <h3 className="text-sm font-bold text-foreground">{certMeta.subject_cn}</h3>
                  {certMeta.subject_cnpj && (
                    <p className="text-xs text-muted-foreground font-mono">CNPJ: {certMeta.subject_cnpj}</p>
                  )}
                </div>

                <div className="text-right">
                  <span className="text-[10px] text-muted-foreground uppercase font-semibold tracking-wider">Validade / Expiração</span>
                  <p className="text-xs font-bold text-foreground font-mono">
                    {new Date(certMeta.valid_until).toLocaleDateString("pt-BR")}
                  </p>
                  <p
                    className={`text-[11px] font-semibold ${
                      certMeta.days_until_expiration < 30 ? "text-amber-500" : "text-emerald-500"
                    }`}
                  >
                    {certMeta.days_until_expiration > 0
                      ? `Vence em ${certMeta.days_until_expiration} dias`
                      : "Expirado"}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] text-muted-foreground">
                <div>
                  <strong>Autoridade Emissora:</strong> {certMeta.issuer}
                </div>
                <div>
                  <strong>Número de Série:</strong> <span className="font-mono">{certMeta.serial_number}</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-6 rounded-xl border border-dashed text-center text-muted-foreground space-y-1">
              <FileCheck className="h-8 w-8 mx-auto text-muted-foreground/60" />
              <p className="font-semibold text-foreground">Nenhum certificado A1 instalado nesta empresa</p>
              <p className="text-[11px]">Faça o upload do arquivo .pfx/.p12 contendo o certificado e a chave privada.</p>
            </div>
          )}

          {/* Upload Form */}
          <form onSubmit={handleUploadCert} className="p-4 rounded-xl bg-muted/30 border border-border space-y-3">
            <h3 className="font-bold text-foreground flex items-center gap-1.5 text-xs">
              <Upload className="h-4 w-4 text-primary" /> Atualizar / Importar Novo Certificado A1
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="font-semibold block mb-1">Arquivo (.pfx ou .p12) *</label>
                <input
                  type="file"
                  accept=".pfx,.p12"
                  onChange={(e) => setCertFile(e.target.files?.[0] || null)}
                  className="w-full text-xs text-foreground file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-primary file:text-primary-foreground hover:file:bg-primary/90 cursor-pointer"
                  required
                />
              </div>

              <div>
                <label className="font-semibold block mb-1">Senha do Certificado *</label>
                <Input
                  type="password"
                  placeholder="Informe a senha do arquivo PFX/P12..."
                  value={certPassword}
                  onChange={(e) => setCertPassword(e.target.value)}
                  className="h-9 text-xs"
                  required
                />
              </div>
            </div>

            <div className="flex justify-end pt-1">
              <Button
                type="submit"
                disabled={uploadingCert || !certFile || !certPassword}
                className="h-9 text-xs bg-emerald-600 hover:bg-emerald-700 text-white gap-1.5 font-semibold"
              >
                <Upload className="h-4 w-4" /> {uploadingCert ? "Validando & Criptografando..." : "Enviar Certificado A1"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* 3. SÉRIES FISCAIS */}
      <Card className="border-border/60 shadow-sm">
        <CardHeader className="pb-3 border-b border-border/60">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-purple-500/10 text-purple-500 flex items-center justify-center font-bold">
                <Layers className="h-4 w-4" />
              </div>
              <div>
                <CardTitle className="text-base font-bold">Séries & Numeração Fiscal</CardTitle>
                <CardDescription className="text-xs">
                  Controle sequencial autorizado para NF-e (Modelo 55), NFC-e (Modelo 65) e NFS-e.
                </CardDescription>
              </div>
            </div>

            <Button
              onClick={() => setIsSeriesModalOpen(true)}
              size="sm"
              className="h-8 text-xs bg-primary gap-1.5 font-semibold"
            >
              <Plus className="h-3.5 w-3.5" /> Cadastrar Série
            </Button>
          </div>
        </CardHeader>

        <CardContent className="p-6">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-muted/50 border-b text-muted-foreground font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-2.5 px-3">Modelo</th>
                  <th className="py-2.5 px-3">Série</th>
                  <th className="py-2.5 px-3">Último Número Autorizado</th>
                  <th className="py-2.5 px-3">Ambiente</th>
                  <th className="py-2.5 px-3 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {seriesList.length > 0 ? (
                  seriesList.map((s) => (
                    <tr key={s.id} className="hover:bg-muted/30 transition-colors">
                      <td className="py-3 px-3 font-bold text-foreground">
                        {s.doc_model === "55" ? "NF-e (Mod. 55)" : s.doc_model === "65" ? "NFC-e (Mod. 65)" : "NFS-e"}
                      </td>
                      <td className="py-3 px-3 font-mono font-semibold text-foreground">Série {s.series}</td>
                      <td className="py-3 px-3 font-mono font-bold text-primary text-sm">{s.current_number}</td>
                      <td className="py-3 px-3">
                        <Badge
                          variant="outline"
                          className={s.environment === "PRODUCTION" ? "border-rose-500/30 text-rose-500" : ""}
                        >
                          {s.environment}
                        </Badge>
                      </td>
                      <td className="py-3 px-3 text-center">
                        <Badge variant={s.is_active ? "success" : "secondary"}>
                          {s.is_active ? "Ativa" : "Inativa"}
                        </Badge>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-muted-foreground">
                      Nenhuma série fiscal cadastrada para a empresa ativa.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Modal Nova Série */}
      {isSeriesModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-md p-6 space-y-4">
            <h3 className="text-sm font-bold text-foreground">Cadastrar / Atualizar Série Fiscal</h3>
            <form onSubmit={handleSaveSeries} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold block mb-1">Modelo de Documento *</label>
                <select
                  value={newSeriesData.doc_model}
                  onChange={(e) => setNewSeriesData({ ...newSeriesData, doc_model: e.target.value })}
                  className="w-full h-9 rounded-md border border-input bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary font-semibold"
                >
                  <option value="55">NF-e (Modelo 55 - Nota Fiscal Eletrônica)</option>
                  <option value="65">NFC-e (Modelo 65 - Consumidor Final)</option>
                  <option value="NFS">NFS-e (Nota de Serviços)</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold block mb-1">Número da Série *</label>
                  <Input
                    type="number"
                    min={1}
                    value={newSeriesData.series}
                    onChange={(e) => setNewSeriesData({ ...newSeriesData, series: parseInt(e.target.value) || 1 })}
                    className="h-9 text-xs font-mono"
                    required
                  />
                </div>

                <div>
                  <label className="font-semibold block mb-1">Número Atual Autorizado *</label>
                  <Input
                    type="number"
                    min={0}
                    value={newSeriesData.current_number}
                    onChange={(e) => setNewSeriesData({ ...newSeriesData, current_number: parseInt(e.target.value) || 0 })}
                    className="h-9 text-xs font-mono font-bold"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="font-semibold block mb-1">Ambiente SEFAZ *</label>
                <select
                  value={newSeriesData.environment}
                  onChange={(e) => setNewSeriesData({ ...newSeriesData, environment: e.target.value as any })}
                  className="w-full h-9 rounded-md border border-input bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary font-semibold"
                >
                  <option value="HOMOLOGATION">Homologação</option>
                  <option value="PRODUCTION">Produção</option>
                </select>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setIsSeriesModalOpen(false)} className="h-8 text-xs">
                  Cancelar
                </Button>
                <Button type="submit" disabled={savingSeries} className="h-8 text-xs bg-primary">
                  {savingSeries ? "Salvando..." : "Salvar Série"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
