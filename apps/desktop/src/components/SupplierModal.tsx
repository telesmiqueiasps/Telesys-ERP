import React, { useState, useEffect } from "react";
import { X, Building2, Phone, MapPin, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Supplier, SupplierCreateInput } from "@/types/customer";
import { customerService } from "@/services/customerService";

interface SupplierModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  supplier?: Supplier | null;
}

export function SupplierModal({ isOpen, onClose, onSuccess, supplier }: SupplierModalProps) {
  const [formData, setFormData] = useState<SupplierCreateInput>({
    name: "",
    trade_name: "",
    document: "",
    state_registration: "",
    phone: "",
    email: "",
    contact_person: "",
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
    if (supplier) {
      setFormData({
        name: supplier.name || "",
        trade_name: supplier.trade_name || "",
        document: supplier.document || "",
        state_registration: supplier.state_registration || "",
        phone: supplier.phone || "",
        email: supplier.email || "",
        contact_person: supplier.contact_person || "",
        address_street: supplier.address_street || "",
        address_number: supplier.address_number || "",
        address_neighborhood: supplier.address_neighborhood || "",
        city: supplier.city || "",
        state: supplier.state || "",
        postal_code: supplier.postal_code || "",
        notes: supplier.notes || "",
        is_active: supplier.is_active,
      });
    } else {
      setFormData({
        name: "",
        trade_name: "",
        document: "",
        state_registration: "",
        phone: "",
        email: "",
        contact_person: "",
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
  }, [supplier, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      setError("A Razão Social do fornecedor é obrigatória.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      if (supplier) {
        await customerService.updateSupplier(supplier.id, formData);
      } else {
        await customerService.createSupplier(formData);
      }
      onSuccess();
      onClose();
    } catch (err: any) {
      console.error("Erro ao salvar fornecedor:", err);
      setError(err?.response?.data?.detail || "Falha ao salvar dados do fornecedor.");
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
            <Building2 className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-bold">
              {supplier ? "Editar Fornecedor" : "Novo Fornecedor"}
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
              <Building2 className="h-3.5 w-3.5 text-primary" /> Identificação da Empresa
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="md:col-span-2">
                <label className="text-xs font-medium text-muted-foreground">Razão Social *</label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Ex: Distribuidora de Alimentos LTDA"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">Nome Fantasia</label>
                <Input
                  value={formData.trade_name || ""}
                  onChange={(e) => setFormData({ ...formData, trade_name: e.target.value })}
                  placeholder="Ex: Distribuidora Alimentos"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">CNPJ / CPF</label>
                <Input
                  value={formData.document || ""}
                  onChange={(e) => setFormData({ ...formData, document: e.target.value })}
                  placeholder="00.000.000/0001-00"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">Inscrição Estadual (IE)</label>
                <Input
                  value={formData.state_registration || ""}
                  onChange={(e) => setFormData({ ...formData, state_registration: e.target.value })}
                  placeholder="ISENTO ou 000.000.000.000"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">Pessoa de Contato / Vendedor</label>
                <Input
                  value={formData.contact_person || ""}
                  onChange={(e) => setFormData({ ...formData, contact_person: e.target.value })}
                  placeholder="Ex: Carlos Oliveira"
                />
              </div>
            </div>
          </div>

          {/* Contato */}
          <div className="space-y-3 pt-2 border-t border-border">
            <h3 className="text-xs font-semibold uppercase text-muted-foreground tracking-wider flex items-center gap-1.5">
              <Phone className="h-3.5 w-3.5 text-primary" /> Contato Operacional
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
                <label className="text-xs font-medium text-muted-foreground">E-mail Comercial</label>
                <Input
                  type="email"
                  value={formData.email || ""}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="vendas@fornecedor.com.br"
                />
              </div>
            </div>
          </div>

          {/* Endereço */}
          <div className="space-y-3 pt-2 border-t border-border">
            <h3 className="text-xs font-semibold uppercase text-muted-foreground tracking-wider flex items-center gap-1.5">
              <MapPin className="h-3.5 w-3.5 text-primary" /> Endereço Comercial
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="md:col-span-2">
                <label className="text-xs font-medium text-muted-foreground">Logradouro / Rua</label>
                <Input
                  value={formData.address_street || ""}
                  onChange={(e) => setFormData({ ...formData, address_street: e.target.value })}
                  placeholder="Rua das Indústrias"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">Número</label>
                <Input
                  value={formData.address_number || ""}
                  onChange={(e) => setFormData({ ...formData, address_number: e.target.value })}
                  placeholder="500"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">Bairro</label>
                <Input
                  value={formData.address_neighborhood || ""}
                  onChange={(e) => setFormData({ ...formData, address_neighborhood: e.target.value })}
                  placeholder="Distrito Industrial"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">Cidade</label>
                <Input
                  value={formData.city || ""}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                  placeholder="Campinas"
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
              <label className="text-xs font-medium text-muted-foreground">Observações / Prazos de Entrega</label>
              <Input
                value={formData.notes || ""}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder="Ex: Entrega em 48h, faturamento 30 dias..."
              />
            </div>

            <div className="flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="is_active_supp"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
              />
              <label htmlFor="is_active_supp" className="text-sm font-medium cursor-pointer">
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
              {loading ? "Salvando..." : supplier ? "Atualizar Fornecedor" : "Cadastrar Fornecedor"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
