import React, { useState, useEffect } from "react";
import { X, User, Phone, MapPin, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Customer, CustomerCreateInput } from "@/types/customer";
import { customerService } from "@/services/customerService";

interface CustomerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  customer?: Customer | null;
}

export function CustomerModal({ isOpen, onClose, onSuccess, customer }: CustomerModalProps) {
  const [formData, setFormData] = useState<CustomerCreateInput>({
    name: "",
    trade_name: "",
    document: "",
    phone: "",
    email: "",
    address_street: "",
    address_number: "",
    address_neighborhood: "",
    city: "",
    state: "",
    postal_code: "",
    notes: "",
    is_active: true,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (customer) {
      setFormData({
        name: customer.name || "",
        trade_name: customer.trade_name || "",
        document: customer.document || "",
        phone: customer.phone || "",
        email: customer.email || "",
        address_street: customer.address_street || "",
        address_number: customer.address_number || "",
        address_neighborhood: customer.address_neighborhood || "",
        city: customer.city || "",
        state: customer.state || "",
        postal_code: customer.postal_code || "",
        notes: customer.notes || "",
        is_active: customer.is_active,
      });
    } else {
      setFormData({
        name: "",
        trade_name: "",
        document: "",
        phone: "",
        email: "",
        address_street: "",
        address_number: "",
        address_neighborhood: "",
        city: "",
        state: "",
        postal_code: "",
        notes: "",
        is_active: true,
      });
    }
    setError(null);
  }, [customer, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      setError("O Nome/Razão Social do cliente é obrigatório.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      if (customer) {
        await customerService.updateCustomer(customer.id, formData);
      } else {
        await customerService.createCustomer(formData);
      }
      onSuccess();
      onClose();
    } catch (err: any) {
      console.error("Erro ao salvar cliente:", err);
      setError(err?.response?.data?.detail || "Falha ao salvar dados do cliente.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-card border border-border rounded-xl shadow-xl w-full max-w-2xl overflow-hidden my-8 animate-in fade-in zoom-in duration-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-muted/40">
          <div className="flex items-center gap-2">
            <User className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-bold">
              {customer ? "Editar Cliente" : "Novo Cliente"}
            </h2>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8 text-muted-foreground">
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 max-h-[80vh] overflow-y-auto">
          {error && (
            <div className="p-3 text-xs bg-destructive/10 border border-destructive/20 text-destructive rounded-lg font-medium">
              {error}
            </div>
          )}

          {/* Dados Principais */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold uppercase text-muted-foreground tracking-wider flex items-center gap-1.5">
              <User className="h-3.5 w-3.5 text-primary" /> Identificação
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="md:col-span-2">
                <label className="text-xs font-medium text-muted-foreground">Nome / Razão Social *</label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Ex: João da Silva / Silva Comércio LTDA"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">Nome Fantasia</label>
                <Input
                  value={formData.trade_name || ""}
                  onChange={(e) => setFormData({ ...formData, trade_name: e.target.value })}
                  placeholder="Ex: Mercado Silva"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">CPF ou CNPJ</label>
                <Input
                  value={formData.document || ""}
                  onChange={(e) => setFormData({ ...formData, document: e.target.value })}
                  placeholder="Ex: 000.000.000-00"
                />
              </div>
            </div>
          </div>

          {/* Contato */}
          <div className="space-y-3 pt-2 border-t border-border">
            <h3 className="text-xs font-semibold uppercase text-muted-foreground tracking-wider flex items-center gap-1.5">
              <Phone className="h-3.5 w-3.5 text-primary" /> Contato
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-muted-foreground">Telefone / WhatsApp</label>
                <Input
                  value={formData.phone || ""}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  placeholder="(00) 90000-0000"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">E-mail</label>
                <Input
                  type="email"
                  value={formData.email || ""}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="cliente@email.com"
                />
              </div>
            </div>
          </div>

          {/* Endereço */}
          <div className="space-y-3 pt-2 border-t border-border">
            <h3 className="text-xs font-semibold uppercase text-muted-foreground tracking-wider flex items-center gap-1.5">
              <MapPin className="h-3.5 w-3.5 text-primary" /> Endereço
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="md:col-span-2">
                <label className="text-xs font-medium text-muted-foreground">Logradouro / Rua</label>
                <Input
                  value={formData.address_street || ""}
                  onChange={(e) => setFormData({ ...formData, address_street: e.target.value })}
                  placeholder="Av. Principal"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">Número</label>
                <Input
                  value={formData.address_number || ""}
                  onChange={(e) => setFormData({ ...formData, address_number: e.target.value })}
                  placeholder="100"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">Bairro</label>
                <Input
                  value={formData.address_neighborhood || ""}
                  onChange={(e) => setFormData({ ...formData, address_neighborhood: e.target.value })}
                  placeholder="Centro"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">Cidade</label>
                <Input
                  value={formData.city || ""}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                  placeholder="São Paulo"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-xs font-medium text-muted-foreground">UF</label>
                  <Input
                    maxLength={2}
                    value={formData.state || ""}
                    onChange={(e) => setFormData({ ...formData, state: e.target.value.toUpperCase() })}
                    placeholder="SP"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">CEP</label>
                  <Input
                    value={formData.postal_code || ""}
                    onChange={(e) => setFormData({ ...formData, postal_code: e.target.value })}
                    placeholder="00000-000"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Observações & Status */}
          <div className="space-y-3 pt-2 border-t border-border">
            <div>
              <label className="text-xs font-medium text-muted-foreground">Observações Internas</label>
              <Input
                value={formData.notes || ""}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder="Preferências do cliente, restrições ou termos..."
              />
            </div>

            <div className="flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="is_active_cust"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
              />
              <label htmlFor="is_active_cust" className="text-sm font-medium cursor-pointer">
                Cadastro Ativo
              </label>
            </div>
          </div>

          {/* Footer Actions */}
          <div className="pt-4 border-t border-border flex items-center justify-end gap-3">
            <Button type="button" variant="outline" onClick={onClose} disabled={loading}>
              Cancelar
            </Button>
            <Button type="submit" disabled={loading} className="gap-2 font-semibold">
              <CheckCircle2 className="h-4 w-4" />
              {loading ? "Salvando..." : customer ? "Atualizar Cliente" : "Cadastrar Cliente"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
