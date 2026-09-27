import React, { useState, useEffect, useCallback } from "react";
import {
  Building2,
  ShieldCheck,
  Laptop,
  DollarSign,
  Plus,
  RefreshCw,
  Search,
  Lock,
  Unlock,
  Edit,
  CheckCircle,
  XCircle,
  Key,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { superadminService } from "@/services/superadminService";

import { TenantAdminSummary, SuperAdminMetrics } from "@/types/superadmin";
import { TenantCreateModal } from "@/components/TenantCreateModal";

export function SuperAdminView() {
  const [tenants, setTenants] = useState<TenantAdminSummary[]>([]);
  const [metrics, setMetrics] = useState<SuperAdminMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "ACTIVE" | "BLOCKED">("ALL");
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingLicense, setEditingLicense] = useState<TenantAdminSummary | null>(null);
  const [editingPlan, setEditingPlan] = useState<string>("PRO");
  const [editingMaxDevices, setEditingMaxDevices] = useState<number>(5);
  const [updating, setUpdating] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [tData, mData] = await Promise.all([
        superadminService.getTenants(),
        superadminService.getMetrics(),
      ]);
      setTenants(tData);
      setMetrics(mData);
    } catch (err) {
      console.error("Erro ao carregar dados do SuperAdmin:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleToggleTenantStatus = async (tenant: TenantAdminSummary) => {
    const action = tenant.is_active ? "bloquear" : "desbloquear";
    if (!window.confirm(`Tem certeza que deseja ${action} o cliente "${tenant.name}"?`)) return;

    try {
      await superadminService.updateTenantStatus(tenant.id, !tenant.is_active);
      await loadData();
    } catch (err: any) {
      alert(err?.message || "Erro ao alterar status do tenant.");
    }
  };

  const handleUpdateLicenseSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingLicense?.license?.id) return;

    setUpdating(true);
    try {
      await superadminService.updateLicense(editingLicense.license.id, {
        plan_name: editingPlan,
        max_devices: editingMaxDevices,
      });
      setEditingLicense(null);
      await loadData();
    } catch (err: any) {
      alert(err?.message || "Erro ao atualizar licença do cliente.");
    } finally {
      setUpdating(false);
    }
  };

  const filteredTenants = tenants.filter((t) => {
    const matchesSearch =
      t.name.toLowerCase().includes(search.toLowerCase()) ||
      (t.document && t.document.includes(search));
    const matchesStatus =
      statusFilter === "ALL" ||
      (statusFilter === "ACTIVE" && t.is_active) ||
      (statusFilter === "BLOCKED" && !t.is_active);
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center font-bold">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight">Painel do Gestor (SuperAdmin)</h1>
          </div>
          <p className="text-sm text-slate-400">
            Gestão centralizada de clientes tenants, assinaturas de planos e controle global de licenças.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={loadData}
            className="text-xs text-slate-400 hover:text-white gap-1.5"
          >
            <RefreshCw className="h-3.5 w-3.5" /> Atualizar
          </Button>
          <Button
            onClick={() => setIsCreateModalOpen(true)}
            className="gap-2 font-semibold shadow-sm text-xs bg-blue-600 hover:bg-blue-500 text-white"
          >
            <Plus className="h-4 w-4" /> Cadastrar Novo Cliente
          </Button>
        </div>
      </div>

      {/* Metrics Cards */}
      {metrics && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
              <span>Total de Clientes</span>
              <Building2 className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-2xl font-extrabold text-white">{metrics.total_tenants}</div>
            <div className="text-[11px] text-slate-500">{metrics.active_tenants} ativos na nuvem</div>
          </Card>

          <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
              <span>Clientes Ativos</span>
              <CheckCircle className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-extrabold text-emerald-400">{metrics.active_tenants}</div>
            <div className="text-[11px] text-emerald-500/80">Com licença em vigor</div>
          </Card>

          <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
              <span>Bloqueados</span>
              <XCircle className="w-4 h-4 text-red-400" />
            </div>
            <div className="text-2xl font-extrabold text-red-400">{metrics.blocked_tenants}</div>
            <div className="text-[11px] text-red-500/80">Acesso suspenso</div>
          </Card>

          <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
              <span>Terminais (PDVs)</span>
              <Laptop className="w-4 h-4 text-indigo-400" />
            </div>
            <div className="text-2xl font-extrabold text-indigo-400">{metrics.active_devices}</div>
            <div className="text-[11px] text-slate-500">De {metrics.total_devices} registrados</div>
          </Card>

          <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
              <span>MRR Estimado</span>
              <DollarSign className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-extrabold text-amber-400">
              R$ {metrics.estimated_mrr.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
            </div>
            <div className="text-[11px] text-amber-500/80">Faturamento recorrente/mês</div>
          </Card>
        </div>
      )}

      {/* Filter Bar */}
      <Card className="p-4 bg-slate-900 border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <Input
            placeholder="Buscar por nome do cliente ou CNPJ..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 text-xs bg-slate-950 border-slate-800 text-white"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <button
            onClick={() => setStatusFilter("ALL")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              statusFilter === "ALL" ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-400 hover:text-white"
            }`}
          >
            Todos ({tenants.length})
          </button>
          <button
            onClick={() => setStatusFilter("ACTIVE")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              statusFilter === "ACTIVE" ? "bg-emerald-600 text-white" : "bg-slate-800 text-slate-400 hover:text-white"
            }`}
          >
            Ativos
          </button>
          <button
            onClick={() => setStatusFilter("BLOCKED")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              statusFilter === "BLOCKED" ? "bg-red-600 text-white" : "bg-slate-800 text-slate-400 hover:text-white"
            }`}
          >
            Bloqueados
          </button>
        </div>
      </Card>

      {/* Tenants Table */}
      <Card className="bg-slate-900 border-slate-800 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400 space-y-3">
            <RefreshCw className="h-6 w-6 animate-spin mx-auto text-blue-400" />
            <p className="text-sm font-medium">Carregando lista de clientes tenants...</p>
          </div>
        ) : filteredTenants.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-sm">
            Nenhum cliente tenant encontrado.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-800/60 text-slate-400 border-b border-slate-800 font-semibold uppercase">
                <tr>
                  <th className="p-3">Cliente / Organização</th>
                  <th className="p-3">CNPJ / CPF</th>
                  <th className="p-3">Plano & Status</th>
                  <th className="p-3">Terminais</th>
                  <th className="p-3">Empresas / Usuários</th>
                  <th className="p-3 text-right">Ações de Gestão</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {filteredTenants.map((t) => {
                  const lic = t.license;
                  return (
                    <tr key={t.id} className="hover:bg-slate-800/30 transition">
                      <td className="p-3">
                        <div className="font-semibold text-white flex items-center gap-2">
                          <Building2 className="w-4 h-4 text-blue-400 flex-shrink-0" />
                          <span>{t.name}</span>
                        </div>
                        <div className="text-[11px] text-slate-500 mt-0.5">
                          Cadastrado em {new Date(t.created_at).toLocaleDateString("pt-BR")}
                        </div>
                      </td>

                      <td className="p-3 font-mono text-slate-400">{t.document || "Não informado"}</td>

                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <span className="font-extrabold text-blue-400">{lic?.plan_name || "PRO"}</span>
                          {t.is_active ? (
                            <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                              ATIVO
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-red-500/10 text-red-400 border border-red-500/20">
                              BLOQUEADO
                            </span>
                          )}
                        </div>
                        <div className="text-[11px] font-mono text-slate-500 mt-0.5">
                          Chave: {lic?.license_key || "Não gerada"}
                        </div>
                      </td>

                      <td className="p-3 font-medium text-slate-300">
                        {lic ? (
                          <span>
                            {lic.active_devices_count} / {lic.max_devices} PDVs
                          </span>
                        ) : (
                          <span>{t.devices_count} PDVs</span>
                        )}
                      </td>

                      <td className="p-3 text-slate-400">
                        {t.companies_count} empresa(s) | {t.users_count} usuário(s)
                      </td>

                      <td className="p-3 text-right">
                        <div className="flex items-center justify-end space-x-2">
                          {lic && (
                            <button
                              onClick={() => {
                                setEditingLicense(t);
                                setEditingPlan(lic.plan_name);
                                setEditingMaxDevices(lic.max_devices);
                              }}
                              className="p-1.5 text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 rounded transition"
                              title="Editar Plano e Limites de Licença"
                            >
                              <Edit className="w-4 h-4" />
                            </button>
                          )}

                          <button
                            onClick={() => handleToggleTenantStatus(t)}
                            className={`p-1.5 rounded transition ${
                              t.is_active
                                ? "text-red-400 hover:bg-red-500/10 hover:text-red-300"
                                : "text-emerald-400 hover:bg-emerald-500/10 hover:text-emerald-300"
                            }`}
                            title={t.is_active ? "Bloquear Cliente" : "Desbloquear Cliente"}
                          >
                            {t.is_active ? <Lock className="w-4 h-4" /> : <Unlock className="w-4 h-4" />}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Modal Cadastro Tenant */}
      <TenantCreateModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={loadData}
      />

      {/* Modal Edição de Licença */}
      {editingLicense && editingLicense.license && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center space-x-2">
                <Key className="w-5 h-5 text-blue-400" />
                <span>Editar Licença: {editingLicense.name}</span>
              </h3>
              <button
                onClick={() => setEditingLicense(null)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleUpdateLicenseSubmit} className="space-y-4 text-xs text-slate-300">
              <div>
                <label className="block text-slate-400 mb-1 font-medium">Plano Contratado</label>
                <select
                  value={editingPlan}
                  onChange={(e) => setEditingPlan(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-850 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="MEI">MEI (Até 2 Terminais)</option>
                  <option value="PRO">PRO (Até 5 Terminais)</option>
                  <option value="ENTERPRISE">ENTERPRISE (Até 20 Terminais)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">Limite Máximo de Terminais (PDVs)</label>
                <input
                  type="number"
                  min={1}
                  max={50}
                  value={editingMaxDevices}
                  onChange={(e) => setEditingMaxDevices(parseInt(e.target.value) || 1)}
                  className="w-full px-3 py-2 bg-slate-850 border border-slate-700 rounded-lg text-white font-mono focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setEditingLicense(null)}
                  className="px-4 py-2 bg-slate-800 text-slate-300 font-medium rounded-lg hover:bg-slate-700 transition"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={updating}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg transition flex items-center space-x-2 disabled:opacity-50"
                >
                  {updating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <span>Salvar Alterações</span>}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
