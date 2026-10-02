import React, { useState } from "react";
import { Building2, User, ShieldCheck, AlertCircle, RefreshCw } from "lucide-react";
import { superadminService } from "@/services/superadminService";
import { TenantCreateInput } from "@/types/superadmin";

interface TenantCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const TenantCreateModal: React.FC<TenantCreateModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [formData, setFormData] = useState<TenantCreateInput>({
    name: "",
    document: "",
    company_name: "",
    trade_name: "",
    cnpj: "",
    admin_name: "",
    admin_email: "",
    admin_password: "",
    plan_name: "PRO",
    max_devices: 5,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await superadminService.createTenant({
        ...formData,
        company_name: formData.company_name || formData.name,
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err?.message || "Erro ao cadastrar novo cliente.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
      <div className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/50">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-blue-500/10 text-blue-400 rounded-lg">
              <Building2 className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Cadastrar Novo Cliente Tenant</h2>
              <p className="text-xs text-slate-400">Onboarding de nova empresa cliente na plataforma</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-slate-800 transition"
          >
            ✕
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 overflow-y-auto flex-1 text-xs text-slate-300">
          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center space-x-2 text-red-400">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Dados da Organização / Cliente */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-blue-400 uppercase tracking-wider flex items-center space-x-1">
              <Building2 className="w-3.5 h-3.5" />
              <span>1. Dados da Organização (Tenant & Empresa)</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 mb-1 font-medium">Nome do Cliente / Organização *</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value, company_name: e.target.value })}
                  placeholder="Ex: Grupo Supermercados Silva"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">CPF / CNPJ Principal</label>
                <input
                  type="text"
                  value={formData.document || ""}
                  onChange={(e) => setFormData({ ...formData, document: e.target.value, cnpj: e.target.value })}
                  placeholder="00.000.000/0001-00"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 font-mono"
                />
              </div>
            </div>
          </div>

          {/* Dados do Administrador Master */}
          <div className="space-y-3 pt-2">
            <h3 className="text-xs font-bold text-blue-400 uppercase tracking-wider flex items-center space-x-1">
              <User className="w-3.5 h-3.5" />
              <span>2. Administrador Master da Conta</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="block text-slate-400 mb-1 font-medium">Nome do Admin *</label>
                <input
                  type="text"
                  required
                  value={formData.admin_name}
                  onChange={(e) => setFormData({ ...formData, admin_name: e.target.value })}
                  placeholder="Ex: João da Silva"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">E-mail de Acesso *</label>
                <input
                  type="email"
                  required
                  value={formData.admin_email}
                  onChange={(e) => setFormData({ ...formData, admin_email: e.target.value })}
                  placeholder="admin@empresa.com.br"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">Senha Inicial *</label>
                <input
                  type="password"
                  required
                  value={formData.admin_password}
                  onChange={(e) => setFormData({ ...formData, admin_password: e.target.value })}
                  placeholder="******"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 font-mono"
                />
              </div>
            </div>
          </div>

          {/* Plano & Licenciamento */}
          <div className="space-y-3 pt-2">
            <h3 className="text-xs font-bold text-blue-400 uppercase tracking-wider flex items-center space-x-1">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>3. Plano de Contratação & Licença</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 mb-1 font-medium">Plano Contratado</label>
                <select
                  value={formData.plan_name}
                  onChange={(e) => setFormData({ ...formData, plan_name: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                >
                  <option value="MEI">Plano MEI (Até 2 Terminais - R$ 99/mês)</option>
                  <option value="PRO">Plano PRO (Até 5 Terminais - R$ 199/mês)</option>
                  <option value="ENTERPRISE">Plano ENTERPRISE (Até 20 Terminais - R$ 499/mês)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">Limite de Terminais (PDVs)</label>
                <input
                  type="number"
                  min={1}
                  max={50}
                  value={formData.max_devices}
                  onChange={(e) => setFormData({ ...formData, max_devices: parseInt(e.target.value) || 1 })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 font-mono"
                />
              </div>
            </div>
          </div>

          {/* Footer Buttons */}
          <div className="pt-4 border-t border-slate-800 flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium rounded-lg transition"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg transition flex items-center space-x-2 disabled:opacity-50"
            >
              {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <span>Cadastrar & Ativar Cliente</span>}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
