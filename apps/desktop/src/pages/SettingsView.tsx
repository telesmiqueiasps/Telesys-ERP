import { useState, useEffect, useCallback } from "react";
import {
  Building2,
  Users,
  Shield,
  Plus,
  Edit,
  RefreshCw,
  Search,
  CheckCircle2,
  UserX,
  Building,
  Key,
  HardDrive,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CompanyItem, UserItem, RoleItem, PermissionItem } from "@/types/settings";
import { settingsService } from "@/services/settingsService";
import { CompanyModal } from "@/components/CompanyModal";
import { UserModal } from "@/components/UserModal";
import { RoleModal } from "@/components/RoleModal";
import { LicenseModal } from "@/components/LicenseModal";
import { BackupModal } from "@/components/BackupModal";
import { useAuthStore } from "@/store/useAuthStore";



export function SettingsView() {
  const { activeCompany } = useAuthStore();
  const [activeTab, setActiveTab] = useState<"companies" | "users" | "roles">("companies");

  // Companies state
  const [companies, setCompanies] = useState<CompanyItem[]>([]);
  const [loadingCompanies, setLoadingCompanies] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState<CompanyItem | null>(null);
  const [isCompanyModalOpen, setIsCompanyModalOpen] = useState(false);

  // Users state
  const [users, setUsers] = useState<UserItem[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserItem | null>(null);
  const [isUserModalOpen, setIsUserModalOpen] = useState(false);

  // Roles & Permissions state
  const [roles, setRoles] = useState<RoleItem[]>([]);
  const [permissions, setPermissions] = useState<PermissionItem[]>([]);
  const [loadingRoles, setLoadingRoles] = useState(false);
  const [selectedRole, setSelectedRole] = useState<RoleItem | null>(null);
  const [isRoleModalOpen, setIsRoleModalOpen] = useState(false);

  // License & Backup modal states
  const [isLicenseModalOpen, setIsLicenseModalOpen] = useState(false);
  const [isBackupModalOpen, setIsBackupModalOpen] = useState(false);


  // Search filter
  const [search, setSearch] = useState("");


  const fetchCompanies = useCallback(async () => {
    setLoadingCompanies(true);
    try {
      const data = await settingsService.getCompanies();
      setCompanies(data);
    } catch (err) {
      console.error("Erro ao carregar empresas:", err);
    } finally {
      setLoadingCompanies(false);
    }
  }, []);

  const fetchUsers = useCallback(async () => {
    setLoadingUsers(true);
    try {
      const data = await settingsService.getUsers();
      setUsers(data);
    } catch (err) {
      console.error("Erro ao carregar usuários:", err);
    } finally {
      setLoadingUsers(false);
    }
  }, []);

  const fetchRolesAndPermissions = useCallback(async () => {
    setLoadingRoles(true);
    try {
      const [rData, pData] = await Promise.all([
        settingsService.getRoles(),
        settingsService.getPermissions(),
      ]);
      setRoles(rData);
      setPermissions(pData);
    } catch (err) {
      console.error("Erro ao carregar cargos e permissões:", err);
    } finally {
      setLoadingRoles(false);
    }
  }, []);

  useEffect(() => {
    fetchCompanies();
    fetchUsers();
    fetchRolesAndPermissions();
  }, [fetchCompanies, fetchUsers, fetchRolesAndPermissions]);

  // Filter lists based on search
  const filteredCompanies = companies.filter(
    (c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      (c.trade_name && c.trade_name.toLowerCase().includes(search.toLowerCase())) ||
      (c.cnpj && c.cnpj.includes(search))
  );

  const filteredUsers = users.filter(
    (u) =>
      u.name.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase())
  );

  const filteredRoles = roles.filter(
    (r) =>
      r.name.toLowerCase().includes(search.toLowerCase()) ||
      (r.description && r.description.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center font-bold">
              <Building2 className="h-5 w-5" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight">Configurações & Administração</h1>
          </div>
          <p className="text-sm text-muted-foreground">
            Gestão de Empresas/Filiais, Usuários/Operadores e Matriz de Permissões (RBAC).
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            onClick={() => setIsBackupModalOpen(true)}
            className="gap-2 font-semibold shadow-sm text-xs border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10 hover:text-emerald-300"
          >
            <HardDrive className="h-4 w-4" /> Backup & Restauração
          </Button>

          <Button
            variant="outline"
            onClick={() => setIsLicenseModalOpen(true)}
            className="gap-2 font-semibold shadow-sm text-xs border-blue-500/30 text-blue-400 hover:bg-blue-500/10 hover:text-blue-300"
          >
            <Key className="h-4 w-4" /> Licenciamento & Terminais
          </Button>


          {activeTab === "companies" && (
            <Button
              onClick={() => {
                setSelectedCompany(null);
                setIsCompanyModalOpen(true);
              }}
              className="gap-2 font-semibold shadow-sm text-xs"
            >
              <Plus className="h-4 w-4" /> Nova Empresa / Filial
            </Button>
          )}

          {activeTab === "users" && (
            <Button
              onClick={() => {
                setSelectedUser(null);
                setIsUserModalOpen(true);
              }}
              className="gap-2 font-semibold shadow-sm text-xs"
            >
              <Plus className="h-4 w-4" /> Novo Usuário / Operador
            </Button>
          )}

          {activeTab === "roles" && (
            <Button
              onClick={() => {
                setSelectedRole(null);
                setIsRoleModalOpen(true);
              }}
              className="gap-2 font-semibold shadow-sm text-xs"
            >
              <Plus className="h-4 w-4" /> Criar Novo Cargo
            </Button>
          )}
        </div>

      </div>

      {/* Tabs Bar & Search */}
      <Card className="p-4 border-border/60 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pb-3 border-b border-border/60">
          <div className="flex items-center p-1 bg-muted/60 rounded-xl border border-border/40 w-full sm:w-auto">
            <button
              onClick={() => setActiveTab("companies")}
              className={`flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                activeTab === "companies"
                  ? "bg-card text-foreground shadow-sm border border-border/40"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Building className="h-4 w-4 text-primary" /> Empresas & Filiais ({companies.length})
            </button>
            <button
              onClick={() => setActiveTab("users")}
              className={`flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                activeTab === "users"
                  ? "bg-card text-foreground shadow-sm border border-border/40"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Users className="h-4 w-4 text-primary" /> Usuários ({users.length})
            </button>
            <button
              onClick={() => setActiveTab("roles")}
              className={`flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                activeTab === "roles"
                  ? "bg-card text-foreground shadow-sm border border-border/40"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Shield className="h-4 w-4 text-primary" /> Cargos & Permissões ({roles.length})
            </button>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              fetchCompanies();
              fetchUsers();
              fetchRolesAndPermissions();
            }}
            className="text-xs text-muted-foreground hover:text-foreground gap-1.5 self-end sm:self-auto"
          >
            <RefreshCw className="h-3.5 w-3.5" /> Atualizar
          </Button>
        </div>

        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Filtrar por nome, CNPJ, e-mail..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 text-xs"
          />
        </div>
      </Card>

      {/* Tab 1: Companies / Filiais */}
      {activeTab === "companies" && (
        <Card className="border-border/60 overflow-hidden shadow-sm">
          {loadingCompanies ? (
            <div className="p-12 text-center text-muted-foreground space-y-3">
              <RefreshCw className="h-6 w-6 animate-spin mx-auto text-primary" />
              <p className="text-sm font-medium">Carregando lista de empresas...</p>
            </div>
          ) : filteredCompanies.length === 0 ? (
            <div className="p-12 text-center text-muted-foreground text-sm">
              Nenhuma empresa cadastrada.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-muted/40 border-b border-border text-muted-foreground text-xs font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4">Razão Social / Fantasia</th>
                    <th className="py-3 px-4">CNPJ / IE</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {filteredCompanies.map((comp) => (
                    <tr key={comp.id} className="hover:bg-muted/30 transition-colors">
                      <td className="py-3 px-4">
                        <div className="font-semibold text-foreground flex items-center gap-2">
                          {comp.name}
                          {activeCompany?.id === comp.id && (
                            <Badge variant="outline" className="text-[10px] bg-emerald-500/10 text-emerald-500 border-emerald-500/20">
                              Empresa Ativa
                            </Badge>
                          )}
                        </div>
                        {comp.trade_name && <div className="text-xs text-muted-foreground">{comp.trade_name}</div>}
                      </td>
                      <td className="py-3 px-4 text-xs font-mono space-y-0.5">
                        <div>{comp.cnpj || "Não informado"}</div>
                        {comp.state_registration && (
                          <div className="text-[11px] text-muted-foreground">IE: {comp.state_registration}</div>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        {comp.is_active ? (
                          <Badge variant="success" className="gap-1 text-[11px]">
                            <CheckCircle2 className="h-3 w-3" /> Ativa
                          </Badge>
                        ) : (
                          <Badge variant="destructive" className="gap-1 text-[11px]">
                            <UserX className="h-3 w-3" /> Inativa
                          </Badge>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground hover:text-foreground"
                          onClick={() => {
                            setSelectedCompany(comp);
                            setIsCompanyModalOpen(true);
                          }}
                          title="Editar Empresa"
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* Tab 2: Users */}
      {activeTab === "users" && (
        <Card className="border-border/60 overflow-hidden shadow-sm">
          {loadingUsers ? (
            <div className="p-12 text-center text-muted-foreground space-y-3">
              <RefreshCw className="h-6 w-6 animate-spin mx-auto text-primary" />
              <p className="text-sm font-medium">Carregando lista de usuários...</p>
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="p-12 text-center text-muted-foreground text-sm">
              Nenhum usuário cadastrado.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-muted/40 border-b border-border text-muted-foreground text-xs font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4">Nome do Usuário</th>
                    <th className="py-3 px-4">E-mail</th>
                    <th className="py-3 px-4">Cargos / Funções</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {filteredUsers.map((usr) => (
                    <tr key={usr.id} className="hover:bg-muted/30 transition-colors">
                      <td className="py-3 px-4 font-semibold text-foreground flex items-center gap-2">
                        {usr.name}
                        {usr.is_superuser && (
                          <Badge variant="outline" className="text-[10px] bg-amber-500/10 text-amber-500 border-amber-500/20">
                            Super Admin
                          </Badge>
                        )}
                      </td>
                      <td className="py-3 px-4 text-xs font-mono text-muted-foreground">{usr.email}</td>
                      <td className="py-3 px-4">
                        <div className="flex flex-wrap gap-1">
                          {usr.roles && usr.roles.length > 0 ? (
                            usr.roles.map((r) => (
                              <Badge key={r.id} variant="secondary" className="text-[10px] bg-primary/10 text-primary border-primary/20">
                                {r.name}
                              </Badge>
                            ))
                          ) : (
                            <span className="text-xs text-muted-foreground italic">Sem cargos</span>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        {usr.is_active ? (
                          <Badge variant="success" className="gap-1 text-[11px]">
                            <CheckCircle2 className="h-3 w-3" /> Ativo
                          </Badge>
                        ) : (
                          <Badge variant="destructive" className="gap-1 text-[11px]">
                            <UserX className="h-3 w-3" /> Inativo
                          </Badge>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground hover:text-foreground"
                          onClick={() => {
                            setSelectedUser(usr);
                            setIsUserModalOpen(true);
                          }}
                          title="Editar Usuário"
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* Tab 3: Roles & Permissions (RBAC) */}
      {activeTab === "roles" && (
        <Card className="border-border/60 overflow-hidden shadow-sm">
          {loadingRoles ? (
            <div className="p-12 text-center text-muted-foreground space-y-3">
              <RefreshCw className="h-6 w-6 animate-spin mx-auto text-primary" />
              <p className="text-sm font-medium">Carregando matriz de cargos e permissões...</p>
            </div>
          ) : filteredRoles.length === 0 ? (
            <div className="p-12 text-center text-muted-foreground text-sm">
              Nenhum cargo cadastrado.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-muted/40 border-b border-border text-muted-foreground text-xs font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4">Nome do Cargo</th>
                    <th className="py-3 px-4">Descrição</th>
                    <th className="py-3 px-4">Permissões Atribuídas</th>
                    <th className="py-3 px-4">Tipo</th>
                    <th className="py-3 px-4 text-right">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {filteredRoles.map((r) => (
                    <tr key={r.id} className="hover:bg-muted/30 transition-colors">
                      <td className="py-3 px-4 font-semibold text-foreground">{r.name}</td>
                      <td className="py-3 px-4 text-xs text-muted-foreground">{r.description || "-"}</td>
                      <td className="py-3 px-4">
                        <Badge variant="outline" className="text-[11px] font-mono">
                          {r.permissions ? r.permissions.length : 0} permissões
                        </Badge>
                      </td>
                      <td className="py-3 px-4">
                        {r.is_system ? (
                          <Badge variant="secondary" className="text-[10px] bg-blue-500/10 text-blue-500 border-blue-500/20">
                            Sistema (Padrão)
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-[10px]">
                            Customizado
                          </Badge>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground hover:text-foreground"
                          onClick={() => {
                            setSelectedRole(r);
                            setIsRoleModalOpen(true);
                          }}
                          title="Ver / Editar Permissões do Cargo"
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
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
      <CompanyModal
        isOpen={isCompanyModalOpen}
        onClose={() => setIsCompanyModalOpen(false)}
        onSuccess={fetchCompanies}
        company={selectedCompany}
      />

      <UserModal
        isOpen={isUserModalOpen}
        onClose={() => setIsUserModalOpen(false)}
        onSuccess={fetchUsers}
        user={selectedUser}
        roles={roles}
      />

      <RoleModal
        isOpen={isRoleModalOpen}
        onClose={() => setIsRoleModalOpen(false)}
        onSuccess={fetchRolesAndPermissions}
        role={selectedRole}
        permissions={permissions}
      />

      <LicenseModal
        isOpen={isLicenseModalOpen}
        onClose={() => setIsLicenseModalOpen(false)}
      />

      <BackupModal
        isOpen={isBackupModalOpen}
        onClose={() => setIsBackupModalOpen(false)}
      />
    </div>
  );
}


