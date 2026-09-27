import React, { useState, useEffect } from "react";
import { X, Building2, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { CompanyItem, CompanyCreateInput } from "@/types/settings";
import { settingsService } from "@/services/settingsService";

interface CompanyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  company?: CompanyItem | null;
}

export function CompanyModal({ isOpen, onClose, onSuccess, company }: CompanyModalProps) {
  const [formData, setFormData] = useState<CompanyCreateInput>({
    name: "",
    trade_name: "",
    cnpj: "",
    state_registration: "",
    is_active: true,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (company) {
      setFormData({
        name: company.name || "",
        trade_name: company.trade_name || "",
        cnpj: company.cnpj || "",
        state_registration: company.state_registration || "",
        is_active: company.is_active,
      });
    } else {
      setFormData({
        name: "",
        trade_name: "",
        cnpj: "",
        state_registration: "",
        is_active: true,
      });
    }
    setError(null);
  }, [company, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      setError("A Razão Social da empresa/filial é obrigatória.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      if (company) {
        await settingsService.updateCompany(company.id, formData);
      } else {
        await settingsService.createCompany(formData);
      }
      onSuccess();
      onClose();
    } catch (err: any) {
      console.error("Erro ao salvar empresa:", err);
      setError(err?.message || "Falha ao salvar dados da empresa.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-muted/40">
          <div className="flex items-center gap-2">
            <Building2 className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-bold">
              {company ? "Editar Empresa / Filial" : "Nova Empresa / Filial"}
            </h2>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8 text-muted-foreground">
            <X className="h-4 w-4" />
          </Button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 text-xs bg-destructive/10 border border-destructive/20 text-destructive rounded-lg font-medium">
              {error}
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground">Razão Social *</label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="Ex: Telesys Tecnologia e Comercio LTDA"
              required
              autoFocus
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground">Nome Fantasia</label>
            <Input
              value={formData.trade_name || ""}
              onChange={(e) => setFormData({ ...formData, trade_name: e.target.value })}
              placeholder="Ex: Telesys Matriz"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground">CNPJ</label>
              <Input
                value={formData.cnpj || ""}
                onChange={(e) => setFormData({ ...formData, cnpj: e.target.value })}
                placeholder="00.000.000/0001-00"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground">Inscrição Estadual (IE)</label>
              <Input
                value={formData.state_registration || ""}
                onChange={(e) => setFormData({ ...formData, state_registration: e.target.value })}
                placeholder="ISENTO ou 000.000.000"
              />
            </div>
          </div>

          <div className="flex items-center gap-2 pt-1">
            <input
              type="checkbox"
              id="is_active_comp"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
            />
            <label htmlFor="is_active_comp" className="text-sm font-medium cursor-pointer">
              Empresa Ativa no Sistema
            </label>
          </div>

          <div className="pt-4 border-t border-border flex items-center justify-end gap-3">
            <Button type="button" variant="outline" onClick={onClose} disabled={loading}>
              Cancelar
            </Button>
            <Button type="submit" disabled={loading} className="gap-2 font-semibold">
              <CheckCircle2 className="h-4 w-4" />
              {loading ? "Salvando..." : company ? "Atualizar Empresa" : "Cadastrar Empresa"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
