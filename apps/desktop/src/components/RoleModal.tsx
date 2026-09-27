import React, { useState, useEffect } from "react";
import { X, Shield, CheckCircle2, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { RoleItem, PermissionItem, RoleCreateInput } from "@/types/settings";
import { settingsService } from "@/services/settingsService";

interface RoleModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  role?: RoleItem | null;
  permissions: PermissionItem[];
}

export function RoleModal({ isOpen, onClose, onSuccess, role, permissions }: RoleModalProps) {
  const [formData, setFormData] = useState<RoleCreateInput>({
    name: "",
    description: "",
    permission_ids: [],
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (role) {
      setFormData({
        name: role.name || "",
        description: role.description || "",
        permission_ids: role.permissions ? role.permissions.map((p) => p.id) : [],
      });
    } else {
      setFormData({
        name: "",
        description: "",
        permission_ids: [],
      });
    }
    setError(null);
  }, [role, isOpen]);

  if (!isOpen) return null;

  const handlePermissionToggle = (permId: string) => {
    setFormData((prev) => {
      const exists = prev.permission_ids.includes(permId);
      if (exists) {
        return { ...prev, permission_ids: prev.permission_ids.filter((id) => id !== permId) };
      } else {
        return { ...prev, permission_ids: [...prev.permission_ids, permId] };
      }
    });
  };

  // Group permissions by module
  const permissionsByModule = permissions.reduce<Record<string, PermissionItem[]>>((acc, perm) => {
    const mod = perm.module || "Outros";
    if (!acc[mod]) acc[mod] = [];
    acc[mod].push(perm);
    return acc;
  }, {});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      setError("O Nome do cargo/função é obrigatório.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await settingsService.createRole(formData);
      onSuccess();
      onClose();
    } catch (err: any) {
      console.error("Erro ao salvar cargo:", err);
      setError(err?.message || "Falha ao salvar cargo.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-2xl overflow-hidden my-8 animate-in fade-in zoom-in duration-200">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-muted/40">
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-bold">
              {role ? "Detalhes do Cargo / Função" : "Novo Cargo & Permissões"}
            </h2>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8 text-muted-foreground">
            <X className="h-4 w-4" />
          </Button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4 max-h-[80vh] overflow-y-auto">
          {error && (
            <div className="p-3 text-xs bg-destructive/10 border border-destructive/20 text-destructive rounded-lg font-medium">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-muted-foreground">Nome do Cargo *</label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Ex: Operador de Caixa / Subgerente"
                required
                disabled={role?.is_system}
                autoFocus
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground">Descrição Breve</label>
              <Input
                value={formData.description || ""}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Ex: Acesso apenas às rotinas do PDV e Caixa"
                disabled={role?.is_system}
              />
            </div>
          </div>

          {/* Matrix Checklist of Permissions */}
          <div className="space-y-3 pt-2 border-t border-border">
            <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <Lock className="h-3.5 w-3.5 text-primary" /> Matriz de Permissões de Acesso
            </label>

            <div className="space-y-4 max-h-72 overflow-y-auto border border-border/60 p-3 rounded-xl bg-muted/20 divide-y divide-border/60">
              {Object.keys(permissionsByModule).map((moduleName) => (
                <div key={moduleName} className="pt-2 first:pt-0 space-y-2">
                  <h4 className="text-xs font-bold text-primary uppercase tracking-wider">
                    Módulo: {moduleName}
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {permissionsByModule[moduleName].map((p) => {
                      const checked = formData.permission_ids.includes(p.id);
                      return (
                        <label
                          key={p.id}
                          className={`flex items-start gap-2 p-2 rounded-lg text-xs cursor-pointer border transition-all ${
                            checked
                              ? "bg-primary/10 border-primary/30 font-semibold text-primary"
                              : "bg-card border-border/40 hover:bg-muted/40 text-foreground"
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={() => handlePermissionToggle(p.id)}
                            disabled={role?.is_system}
                            className="h-4 w-4 mt-0.5 rounded border-border text-primary focus:ring-primary"
                          />
                          <div>
                            <span className="block font-medium">{p.name}</span>
                            <span className="text-[10px] text-muted-foreground font-mono block">
                              {p.code}
                            </span>
                          </div>
                        </label>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-border flex items-center justify-end gap-3">
            <Button type="button" variant="outline" onClick={onClose} disabled={loading}>
              Cancelar
            </Button>
            {!role?.is_system && (
              <Button type="submit" disabled={loading} className="gap-2 font-semibold">
                <CheckCircle2 className="h-4 w-4" />
                {loading ? "Salvando..." : "Salvar Cargo & Permissões"}
              </Button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
