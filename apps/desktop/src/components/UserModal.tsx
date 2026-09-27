import React, { useState, useEffect } from "react";
import { X, User, CheckCircle2, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { UserItem, RoleItem, UserCreateInput } from "@/types/settings";
import { settingsService } from "@/services/settingsService";

interface UserModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  user?: UserItem | null;
  roles: RoleItem[];
}

export function UserModal({ isOpen, onClose, onSuccess, user, roles }: UserModalProps) {
  const [formData, setFormData] = useState<UserCreateInput>({
    name: "",
    email: "",
    password: "",
    is_active: true,
    is_superuser: false,
    role_ids: [],
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      setFormData({
        name: user.name || "",
        email: user.email || "",
        password: "", // Optional for updates
        is_active: user.is_active,
        is_superuser: user.is_superuser,
        role_ids: user.roles ? user.roles.map((r) => r.id) : [],
      });
    } else {
      setFormData({
        name: "",
        email: "",
        password: "",
        is_active: true,
        is_superuser: false,
        role_ids: [],
      });
    }
    setError(null);
  }, [user, isOpen]);

  if (!isOpen) return null;

  const handleRoleToggle = (roleId: string) => {
    setFormData((prev) => {
      const exists = prev.role_ids.includes(roleId);
      if (exists) {
        return { ...prev, role_ids: prev.role_ids.filter((id) => id !== roleId) };
      } else {
        return { ...prev, role_ids: [...prev.role_ids, roleId] };
      }
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      setError("O Nome do usuário é obrigatório.");
      return;
    }
    if (!formData.email.trim()) {
      setError("O E-mail é obrigatório.");
      return;
    }
    if (!user && !formData.password.trim()) {
      setError("A Senha inicial é obrigatória para novos usuários.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      if (user) {
        await settingsService.updateUser(user.id, {
          name: formData.name,
          email: formData.email,
          password: formData.password.trim() || undefined,
          is_active: formData.is_active,
          is_superuser: formData.is_superuser,
          role_ids: formData.role_ids,
        });
      } else {
        await settingsService.createUser(formData);
      }
      onSuccess();
      onClose();
    } catch (err: any) {
      console.error("Erro ao salvar usuário:", err);
      setError(err?.message || "Falha ao salvar usuário.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-lg overflow-hidden my-8 animate-in fade-in zoom-in duration-200">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-muted/40">
          <div className="flex items-center gap-2">
            <User className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-bold">
              {user ? "Editar Usuário / Operador" : "Novo Usuário / Operador"}
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

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground">Nome Completo *</label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="Ex: Carlos Oliveira"
              required
              autoFocus
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground">E-mail de Acesso *</label>
            <Input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="operador@telesys.com.br"
              required
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground">
              {user ? "Nova Senha (Deixe em branco para não alterar)" : "Senha Inicial *"}
            </label>
            <Input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              placeholder="••••••••"
              required={!user}
            />
          </div>

          {/* Role selection */}
          <div className="space-y-2 pt-2 border-t border-border">
            <label className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
              <Shield className="h-3.5 w-3.5 text-primary" /> Atribuir Cargos (Funções)
            </label>
            <div className="space-y-1.5 max-h-40 overflow-y-auto border border-border/60 p-2 rounded-lg bg-muted/20">
              {roles.map((r) => {
                const checked = formData.role_ids.includes(r.id);
                return (
                  <label
                    key={r.id}
                    className={`flex items-center gap-2 p-2 rounded text-xs cursor-pointer transition-colors ${
                      checked ? "bg-primary/10 font-semibold text-primary" : "hover:bg-muted/40"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => handleRoleToggle(r.id)}
                      className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                    />
                    <div>
                      <span>{r.name}</span>
                      {r.description && <span className="text-[10px] text-muted-foreground block">{r.description}</span>}
                    </div>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Toggles */}
          <div className="space-y-2 pt-2 border-t border-border">
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_active_usr"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
              />
              <label htmlFor="is_active_usr" className="text-sm font-medium cursor-pointer">
                Usuário Ativo no Sistema
              </label>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_super_usr"
                checked={formData.is_superuser}
                onChange={(e) => setFormData({ ...formData, is_superuser: e.target.checked })}
                className="h-4 w-4 rounded border-border text-amber-500 focus:ring-amber-500"
              />
              <label htmlFor="is_super_usr" className="text-sm font-semibold text-amber-500 cursor-pointer">
                Administrador Global (Superuser)
              </label>
            </div>
          </div>

          <div className="pt-4 border-t border-border flex items-center justify-end gap-3">
            <Button type="button" variant="outline" onClick={onClose} disabled={loading}>
              Cancelar
            </Button>
            <Button type="submit" disabled={loading} className="gap-2 font-semibold">
              <CheckCircle2 className="h-4 w-4" />
              {loading ? "Salvando..." : user ? "Atualizar Usuário" : "Cadastrar Usuário"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
