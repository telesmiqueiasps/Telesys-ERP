import {
  Building2,
  Users,
  ShieldCheck,
  ShoppingCart,
  Package,
  DollarSign,
  Database,
  ArrowUpRight,
  CheckCircle2,
} from "lucide-react";
import { useAuthStore } from "@/store/useAuthStore";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LocalDbStatusCard } from "@/components/LocalDbStatusCard";

interface DashboardViewProps {
  onNavigate?: (module: string) => void;
}

export function DashboardView({ onNavigate }: DashboardViewProps) {
  const { user, activeCompany } = useAuthStore();

  const moduleCards = [
    {
      id: "pdv",
      title: "PDV — Frente de Caixa",
      description: "Operação rápida de caixa, código de barras, atalhos F1-F12 e emissão de comprovantes.",
      icon: ShoppingCart,
      color: "bg-blue-500/10 text-blue-500 border-blue-500/20",
    },
    {
      id: "estoque",
      title: "Estoque & Produtos",
      description: "Catálogo de produtos, código de barras, entradas, saídas e controle de saldo mínimo.",
      icon: Package,
      color: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
    },
    {
      id: "financeiro",
      title: "Financeiro & Caixa",
      description: "Contas a pagar, contas a receber, fluxo de caixa e controle de sangria/suprimentos.",
      icon: DollarSign,
      color: "bg-purple-500/10 text-purple-500 border-purple-500/20",
    },
    {
      id: "cadastros",
      title: "Cadastros",
      description: "Gestão de clientes, fornecedores, empresas do tenant e credenciais de usuários.",
      icon: Users,
      color: "bg-amber-500/10 text-amber-500 border-amber-500/20",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 text-white border border-slate-700/60 shadow-xl relative overflow-hidden">
        <div className="absolute -top-12 -right-12 w-64 h-64 bg-primary/20 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="bg-primary/20 text-blue-300 border-primary/30">
                Fundação Validada • Etapa 4 (Banco Local)
              </Badge>
              {user?.is_superuser && (
                <Badge variant="outline" className="border-amber-500/40 text-amber-400 bg-amber-500/10">
                  <ShieldCheck className="h-3 w-3 mr-1" /> Super Admin
                </Badge>
              )}
            </div>
            <h2 className="text-2xl font-bold tracking-tight">
              Bem-vindo, {user?.name || "Usuário"}!
            </h2>
            <p className="text-sm text-slate-300">
              Sessão autenticada via JWT & Argon2id com acesso às empresas do Tenant{" "}
              <strong className="text-white font-semibold">{user?.tenant?.name}</strong>.
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Button
              className="gap-2 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold shadow-md"
              onClick={() => onNavigate && onNavigate("pdv")}
            >
              <ShoppingCart className="h-4 w-4" /> Abrir Frente de Caixa
            </Button>
          </div>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-border/60">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Tenant Ativo
            </CardTitle>
            <Building2 className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-lg font-bold truncate">{user?.tenant?.name || "Não selecionado"}</div>
            <p className="text-xs text-muted-foreground mt-1">ID: {user?.tenant_id?.slice(0, 8)}...</p>
          </CardContent>
        </Card>

        <Card className="border-border/60">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Empresa Selecionada
            </CardTitle>
            <Building2 className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-lg font-bold truncate">{activeCompany?.name || "Matriz"}</div>
            <p className="text-xs text-emerald-600 dark:text-emerald-400 font-medium mt-1">
              CNPJ: {activeCompany?.cnpj || "00.000.000/0001-00"}
            </p>
          </CardContent>
        </Card>

        <Card className="border-border/60">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Permissões Concedidas
            </CardTitle>
            <ShieldCheck className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{user?.permissions?.length || 0}</div>
            <p className="text-xs text-muted-foreground mt-1">Regras de Acesso RBAC Ativas</p>
          </CardContent>
        </Card>

        <Card className="border-border/60">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Arquitetura de Dados
            </CardTitle>
            <Database className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-lg font-bold text-amber-600 dark:text-amber-400">Local-First (Etapa 4)</div>
            <p className="text-xs text-muted-foreground mt-1">SQLite Master & Empresa Ativa</p>
          </CardContent>
        </Card>
      </div>

      {/* Local Database Status & Architecture Component */}
      <LocalDbStatusCard />

      {/* Functional Modules Section */}
      <div className="space-y-3">
        <h3 className="text-base font-bold tracking-tight">Módulos do Sistema</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {moduleCards.map((mod) => {
            const Icon = mod.icon;
            return (
              <Card
                key={mod.id}
                className="border-border/60 hover:border-primary/50 transition-all duration-200 cursor-pointer group"
                onClick={() => onNavigate && onNavigate(mod.id)}
              >
                <CardContent className="p-5 flex items-start gap-4">
                  <div className={`p-3 rounded-xl border ${mod.color}`}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center justify-between">
                      <h4 className="font-bold text-base group-hover:text-primary transition-colors">
                        {mod.title}
                      </h4>
                      <ArrowUpRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed">{mod.description}</p>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Permissions Badges List */}
      {user?.permissions && user.permissions.length > 0 && (
        <Card className="border-border/60">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-bold flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-500" /> Catálogo de Permissões Habilitadas no RBAC
            </CardTitle>
            <CardDescription className="text-xs">
              Códigos de autorização verificados dinamicamente para o usuário {user.name}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-1.5">
            {user.permissions.map((perm) => (
              <Badge key={perm} variant="secondary" className="font-mono text-[11px] py-0.5 px-2">
                {perm}
              </Badge>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
