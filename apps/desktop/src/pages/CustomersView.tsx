import { useState, useEffect, useCallback } from "react";
import {
  Users,
  Building2,
  Search,
  Plus,
  Edit,
  Power,
  Phone,
  Mail,
  MapPin,
  RefreshCw,
  UserCheck,
  UserX,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Customer, Supplier } from "@/types/customer";
import { customerService } from "@/services/customerService";
import { CustomerModal } from "@/components/CustomerModal";
import { SupplierModal } from "@/components/SupplierModal";
import { useAuthStore } from "@/store/useAuthStore";

export function CustomersView() {
  const { activeCompany } = useAuthStore();
  const [activeTab, setActiveTab] = useState<"customers" | "suppliers">("customers");

  // State for Customers
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loadingCustomers, setLoadingCustomers] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [isCustomerModalOpen, setIsCustomerModalOpen] = useState(false);

  // State for Suppliers
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loadingSuppliers, setLoadingSuppliers] = useState(false);
  const [selectedSupplier, setSelectedSupplier] = useState<Supplier | null>(null);
  const [isSupplierModalOpen, setIsSupplierModalOpen] = useState(false);

  // Filter States
  const [search, setSearch] = useState("");
  const [activeFilter, setActiveFilter] = useState<"all" | "active" | "inactive">("active");

  // Fetch Customers
  const fetchCustomers = useCallback(async () => {
    if (!activeCompany) return;
    setLoadingCustomers(true);
    try {
      const isActiveParam = activeFilter === "all" ? undefined : activeFilter === "active";
      const data = await customerService.getCustomers(activeCompany.id, search, isActiveParam);
      setCustomers(data);
    } catch (err) {
      console.error("Erro ao carregar clientes:", err);
    } finally {
      setLoadingCustomers(false);
    }
  }, [activeCompany, search, activeFilter]);

  // Fetch Suppliers
  const fetchSuppliers = useCallback(async () => {
    if (!activeCompany) return;
    setLoadingSuppliers(true);
    try {
      const isActiveParam = activeFilter === "all" ? undefined : activeFilter === "active";
      const data = await customerService.getSuppliers(activeCompany.id, search, isActiveParam);
      setSuppliers(data);
    } catch (err) {
      console.error("Erro ao carregar fornecedores:", err);
    } finally {
      setLoadingSuppliers(false);
    }
  }, [activeCompany, search, activeFilter]);

  useEffect(() => {
    if (activeTab === "customers") {
      fetchCustomers();
    } else {
      fetchSuppliers();
    }
  }, [activeTab, fetchCustomers, fetchSuppliers]);

  // Toggle Customer Active Status
  const handleToggleCustomerActive = async (cust: Customer) => {
    try {
      await customerService.updateCustomer(cust.id, { is_active: !cust.is_active });
      fetchCustomers();
    } catch (err) {
      console.error("Erro ao alterar status do cliente:", err);
    }
  };

  // Toggle Supplier Active Status
  const handleToggleSupplierActive = async (supp: Supplier) => {
    try {
      await customerService.updateSupplier(supp.id, { is_active: !supp.is_active });
      fetchSuppliers();
    } catch (err) {
      console.error("Erro ao alterar status do fornecedor:", err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header section with Tabs & Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center font-bold">
              <Users className="h-5 w-5" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight">Cadastros Operacionais</h1>
          </div>
          <p className="text-sm text-muted-foreground">
            Gestão de Clientes (PF/PJ) e Fornecedores parceiros para vendas e notas fiscais.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {activeTab === "customers" ? (
            <Button
              onClick={() => {
                setSelectedCustomer(null);
                setIsCustomerModalOpen(true);
              }}
              className="gap-2 font-semibold shadow-sm"
            >
              <Plus className="h-4 w-4" /> Novo Cliente
            </Button>
          ) : (
            <Button
              onClick={() => {
                setSelectedSupplier(null);
                setIsSupplierModalOpen(true);
              }}
              className="gap-2 font-semibold shadow-sm"
            >
              <Plus className="h-4 w-4" /> Novo Fornecedor
            </Button>
          )}
        </div>
      </div>

      {/* Tabs navigation & search filter bar */}
      <Card className="p-4 border-border/60 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pb-3 border-b border-border/60">
          {/* Main Module Tabs */}
          <div className="flex items-center p-1 bg-muted/60 rounded-xl border border-border/40 w-full sm:w-auto">
            <button
              onClick={() => setActiveTab("customers")}
              className={`flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                activeTab === "customers"
                  ? "bg-card text-foreground shadow-sm border border-border/40"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Users className="h-4 w-4 text-primary" /> Clientes
            </button>
            <button
              onClick={() => setActiveTab("suppliers")}
              className={`flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                activeTab === "suppliers"
                  ? "bg-card text-foreground shadow-sm border border-border/40"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Building2 className="h-4 w-4 text-primary" /> Fornecedores
            </button>
          </div>

          {/* Quick Refresh */}
          <Button
            variant="ghost"
            size="sm"
            onClick={activeTab === "customers" ? fetchCustomers : fetchSuppliers}
            className="text-xs text-muted-foreground hover:text-foreground gap-1.5 self-end sm:self-auto"
          >
            <RefreshCw className="h-3.5 w-3.5" /> Atualizar
          </Button>
        </div>

        {/* Search Input & Status Filters */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="md:col-span-2 relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder={
                activeTab === "customers"
                  ? "Buscar cliente por nome, CPF/CNPJ, telefone ou e-mail..."
                  : "Buscar fornecedor por razão social, CNPJ, contato..."
              }
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>

          <div className="flex items-center gap-1.5 bg-muted/30 p-1 rounded-lg border border-border/40 justify-center">
            <button
              onClick={() => setActiveFilter("active")}
              className={`flex-1 py-1.5 px-3 rounded text-xs font-semibold transition-colors ${
                activeFilter === "active"
                  ? "bg-primary/10 text-primary border border-primary/20"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Ativos
            </button>
            <button
              onClick={() => setActiveFilter("inactive")}
              className={`flex-1 py-1.5 px-3 rounded text-xs font-semibold transition-colors ${
                activeFilter === "inactive"
                  ? "bg-destructive/10 text-destructive border border-destructive/20"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Inativos
            </button>
            <button
              onClick={() => setActiveFilter("all")}
              className={`flex-1 py-1.5 px-3 rounded text-xs font-semibold transition-colors ${
                activeFilter === "all"
                  ? "bg-card text-foreground border border-border"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Todos
            </button>
          </div>
        </div>
      </Card>

      {/* Content Table for Customers */}
      {activeTab === "customers" && (
        <Card className="border-border/60 overflow-hidden shadow-sm">
          {loadingCustomers ? (
            <div className="p-12 text-center text-muted-foreground space-y-3">
              <RefreshCw className="h-6 w-6 animate-spin mx-auto text-primary" />
              <p className="text-sm font-medium">Carregando lista de clientes...</p>
            </div>
          ) : customers.length === 0 ? (
            <div className="p-12 text-center space-y-3">
              <Users className="h-10 w-10 text-muted-foreground/50 mx-auto" />
              <h3 className="text-base font-semibold">Nenhum cliente encontrado</h3>
              <p className="text-xs text-muted-foreground max-w-sm mx-auto">
                Não foram encontrados clientes cadastrados com os filtros selecionados.
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSelectedCustomer(null);
                  setIsCustomerModalOpen(true);
                }}
                className="gap-2 text-xs"
              >
                <Plus className="h-3.5 w-3.5" /> Cadastrar Primeiro Cliente
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-muted/40 border-b border-border text-muted-foreground text-xs font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4">Cliente / Razão Social</th>
                    <th className="py-3 px-4">Documento (CPF/CNPJ)</th>
                    <th className="py-3 px-4">Contato</th>
                    <th className="py-3 px-4">Cidade / UF</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {customers.map((cust) => (
                    <tr key={cust.id} className="hover:bg-muted/30 transition-colors">
                      <td className="py-3 px-4">
                        <div className="font-semibold text-foreground">{cust.name}</div>
                        {cust.trade_name && (
                          <div className="text-xs text-muted-foreground">{cust.trade_name}</div>
                        )}
                      </td>
                      <td className="py-3 px-4 font-mono text-xs">
                        {cust.document || <span className="text-muted-foreground italic">Não informado</span>}
                      </td>
                      <td className="py-3 px-4 text-xs space-y-0.5">
                        {cust.phone && (
                          <div className="flex items-center gap-1 text-muted-foreground">
                            <Phone className="h-3 w-3 text-primary" /> {cust.phone}
                          </div>
                        )}
                        {cust.email && (
                          <div className="flex items-center gap-1 text-muted-foreground">
                            <Mail className="h-3 w-3 text-primary" /> {cust.email}
                          </div>
                        )}
                        {!cust.phone && !cust.email && (
                          <span className="text-muted-foreground italic">Sem contato</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-xs">
                        {cust.city ? (
                          <span className="flex items-center gap-1 text-muted-foreground">
                            <MapPin className="h-3 w-3" /> {cust.city}
                            {cust.state ? ` - ${cust.state}` : ""}
                          </span>
                        ) : (
                          <span className="text-muted-foreground italic">Não informado</span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        {cust.is_active ? (
                          <Badge variant="success" className="gap-1 text-[11px] font-medium">
                            <UserCheck className="h-3 w-3" /> Ativo
                          </Badge>
                        ) : (
                          <Badge variant="destructive" className="gap-1 text-[11px] font-medium">
                            <UserX className="h-3 w-3" /> Inativo
                          </Badge>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-muted-foreground hover:text-foreground"
                            onClick={() => {
                              setSelectedCustomer(cust);
                              setIsCustomerModalOpen(true);
                            }}
                            title="Editar Cliente"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className={`h-8 w-8 ${
                              cust.is_active
                                ? "text-muted-foreground hover:text-destructive"
                                : "text-muted-foreground hover:text-emerald-500"
                            }`}
                            onClick={() => handleToggleCustomerActive(cust)}
                            title={cust.is_active ? "Inativar Cliente" : "Ativar Cliente"}
                          >
                            <Power className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* Content Table for Suppliers */}
      {activeTab === "suppliers" && (
        <Card className="border-border/60 overflow-hidden shadow-sm">
          {loadingSuppliers ? (
            <div className="p-12 text-center text-muted-foreground space-y-3">
              <RefreshCw className="h-6 w-6 animate-spin mx-auto text-primary" />
              <p className="text-sm font-medium">Carregando lista de fornecedores...</p>
            </div>
          ) : suppliers.length === 0 ? (
            <div className="p-12 text-center space-y-3">
              <Building2 className="h-10 w-10 text-muted-foreground/50 mx-auto" />
              <h3 className="text-base font-semibold">Nenhum fornecedor encontrado</h3>
              <p className="text-xs text-muted-foreground max-w-sm mx-auto">
                Não foram encontrados fornecedores cadastrados com os filtros selecionados.
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSelectedSupplier(null);
                  setIsSupplierModalOpen(true);
                }}
                className="gap-2 text-xs"
              >
                <Plus className="h-3.5 w-3.5" /> Cadastrar Primeiro Fornecedor
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-muted/40 border-b border-border text-muted-foreground text-xs font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4">Razão Social / Fantasia</th>
                    <th className="py-3 px-4">CNPJ / IE</th>
                    <th className="py-3 px-4">Contato / Vendedor</th>
                    <th className="py-3 px-4">Cidade / UF</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {suppliers.map((supp) => (
                    <tr key={supp.id} className="hover:bg-muted/30 transition-colors">
                      <td className="py-3 px-4">
                        <div className="font-semibold text-foreground">{supp.name}</div>
                        {supp.trade_name && (
                          <div className="text-xs text-muted-foreground">{supp.trade_name}</div>
                        )}
                      </td>
                      <td className="py-3 px-4 text-xs space-y-0.5">
                        <div className="font-mono">{supp.document || "Não informado"}</div>
                        {supp.state_registration && (
                          <div className="text-[11px] text-muted-foreground">IE: {supp.state_registration}</div>
                        )}
                      </td>
                      <td className="py-3 px-4 text-xs space-y-0.5">
                        {supp.contact_person && (
                          <div className="font-medium text-foreground">{supp.contact_person}</div>
                        )}
                        {supp.phone && (
                          <div className="flex items-center gap-1 text-muted-foreground">
                            <Phone className="h-3 w-3 text-primary" /> {supp.phone}
                          </div>
                        )}
                        {supp.email && (
                          <div className="flex items-center gap-1 text-muted-foreground">
                            <Mail className="h-3 w-3 text-primary" /> {supp.email}
                          </div>
                        )}
                      </td>
                      <td className="py-3 px-4 text-xs">
                        {supp.city ? (
                          <span className="flex items-center gap-1 text-muted-foreground">
                            <MapPin className="h-3 w-3" /> {supp.city}
                            {supp.state ? ` - ${supp.state}` : ""}
                          </span>
                        ) : (
                          <span className="text-muted-foreground italic">Não informado</span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        {supp.is_active ? (
                          <Badge variant="success" className="gap-1 text-[11px] font-medium">
                            <UserCheck className="h-3 w-3" /> Ativo
                          </Badge>
                        ) : (
                          <Badge variant="destructive" className="gap-1 text-[11px] font-medium">
                            <UserX className="h-3 w-3" /> Inativo
                          </Badge>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-muted-foreground hover:text-foreground"
                            onClick={() => {
                              setSelectedSupplier(supp);
                              setIsSupplierModalOpen(true);
                            }}
                            title="Editar Fornecedor"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className={`h-8 w-8 ${
                              supp.is_active
                                ? "text-muted-foreground hover:text-destructive"
                                : "text-muted-foreground hover:text-emerald-500"
                            }`}
                            onClick={() => handleToggleSupplierActive(supp)}
                            title={supp.is_active ? "Inativar Fornecedor" : "Ativar Fornecedor"}
                          >
                            <Power className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* Modals */}
      <CustomerModal
        isOpen={isCustomerModalOpen}
        onClose={() => setIsCustomerModalOpen(false)}
        onSuccess={fetchCustomers}
        customer={selectedCustomer}
      />

      <SupplierModal
        isOpen={isSupplierModalOpen}
        onClose={() => setIsSupplierModalOpen(false)}
        onSuccess={fetchSuppliers}
        supplier={selectedSupplier}
      />
    </div>
  );
}
