import React, { useState, useEffect } from "react";
import {
  Layers,
  LayoutDashboard,
  ShoppingCart,
  Package,
  ShoppingBag,
  DollarSign,
  Users,
  Settings,
  ShieldCheck,
  LogOut,
  Building2,
  ChevronLeft,
  ChevronRight,
  Sun,
  Moon,
  Wifi,
  WifiOff,
  RefreshCw,
  AlertCircle,
  ChevronDown,
  BarChart3,
} from "lucide-react";
import { useAuthStore } from "@/store/useAuthStore";
import { useAppStore } from "@/store/useAppStore";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CompanySelectorModal } from "@/components/CompanySelectorModal";
import { SyncStatusModal } from "@/components/SyncStatusModal";
import { UpdateModal } from "@/components/UpdateModal";
import { syncEngine } from "@/services/syncEngine";
import { updaterService } from "@/services/updaterService";
import { SyncStatusStats } from "@/types/sync";
import { UpdateCheckResponse } from "@/types/updater";

interface AppLayoutProps {
  children: React.ReactNode;
  activeModule?: string;
  onNavigate?: (module: string) => void;
}

export function AppLayout({ children, activeModule = "dashboard", onNavigate }: AppLayoutProps) {
  const { user, activeCompany, logout } = useAuthStore();
  const { theme, toggleTheme, isSidebarOpen, toggleSidebar } = useAppStore();
  const [isCompanyModalOpen, setIsCompanyModalOpen] = useState(false);
  const [isSyncModalOpen, setIsSyncModalOpen] = useState(false);
  const [syncStats, setSyncStats] = useState<SyncStatusStats>(syncEngine.getStats());

  const [updateData, setUpdateData] = useState<UpdateCheckResponse | null>(null);
  const [isUpdateModalOpen, setIsUpdateModalOpen] = useState(false);

  useEffect(() => {
    // Iniciar background worker de sincronização offline-first
    const stopWorker = syncEngine.startWorker(12000);
    const unsubscribe = syncEngine.subscribe((stats) => {
      setSyncStats(stats);
    });

    // Check silencioso de atualização do aplicativo
    updaterService.checkForUpdates()
      .then((data) => {
        if (data.update_available) {
          setUpdateData(data);
          setIsUpdateModalOpen(true);
        }
      })
      .catch(() => {});

    return () => {
      stopWorker();
      unsubscribe();
    };
  }, []);


  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "pdv", label: "PDV (Frente de Caixa)", icon: ShoppingCart },
    { id: "estoque", label: "Estoque & Produtos", icon: Package },
    { id: "compras", label: "Compras & Entradas", icon: ShoppingBag },
    { id: "financeiro", label: "Financeiro & Caixa", icon: DollarSign },
    { id: "relatorios", label: "Relatórios & BI", icon: BarChart3 },
    { id: "cadastros", label: "Cadastros & Clientes", icon: Users },
    { id: "auditoria", label: "Auditoria & Logs", icon: ShieldCheck },
    { id: "configuracoes", label: "Configurações", icon: Settings },
  ];


  if (user?.is_superuser) {
    navItems.push({ id: "superadmin", label: "Gestão SuperAdmin", icon: ShieldCheck });
  }


  return (
    <div className="min-h-screen flex bg-background text-foreground transition-colors duration-200">
      {/* Sidebar */}
      <aside
        className={`bg-card border-r border-border flex flex-col justify-between transition-all duration-300 z-40 ${
          isSidebarOpen ? "w-64" : "w-16"
        }`}
      >
        {/* Top Brand */}
        <div>
          <div className="h-16 border-b border-border flex items-center justify-between px-4">
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="h-9 w-9 shrink-0 rounded-lg bg-primary/10 text-primary flex items-center justify-center font-bold">
                <Layers className="h-5 w-5" />
              </div>
              {isSidebarOpen && (
                <div className="flex flex-col truncate">
                  <span className="font-bold text-sm tracking-tight truncate">Telesys ERP</span>
                  <span className="text-[10px] text-muted-foreground truncate">Desktop Local-First</span>
                </div>
              )}
            </div>

            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 text-muted-foreground hover:text-foreground hidden md:flex"
              onClick={toggleSidebar}
            >
              {isSidebarOpen ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            </Button>
          </div>

          {/* Navigation Items */}
          <nav className="p-2 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeModule === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onNavigate && onNavigate(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-primary text-primary-foreground font-semibold shadow-sm"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  }`}
                  title={!isSidebarOpen ? item.label : undefined}
                >
                  <Icon className="h-5 w-5 shrink-0" />
                  {isSidebarOpen && <span className="truncate">{item.label}</span>}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer (Active Company & User info) */}
        <div className="p-3 border-t border-border space-y-2">
          {isSidebarOpen && (
            <button
              onClick={() => setIsCompanyModalOpen(true)}
              className="w-full p-2.5 rounded-lg bg-muted/50 hover:bg-muted border text-xs text-left space-y-1 transition-colors group"
            >
              <div className="flex items-center justify-between text-muted-foreground font-medium">
                <span className="flex items-center gap-1.5">
                  <Building2 className="h-3.5 w-3.5 text-primary" /> Empresa Ativa
                </span>
                <ChevronDown className="h-3.5 w-3.5 text-muted-foreground group-hover:text-foreground transition-colors" />
              </div>
              <p className="font-semibold text-foreground truncate">
                {activeCompany?.name || "Selecionar Empresa"}
              </p>
              {activeCompany?.cnpj && (
                <p className="text-[10px] text-muted-foreground">{activeCompany.cnpj}</p>
              )}
            </button>
          )}

          <Button
            variant="outline"
            className={`w-full justify-start text-destructive hover:text-destructive hover:bg-destructive/10 border-destructive/20 gap-2 text-xs ${
              !isSidebarOpen ? "px-2 justify-center" : ""
            }`}
            onClick={logout}
            title="Sair do sistema"
          >
            <LogOut className="h-4 w-4 shrink-0" />
            {isSidebarOpen && <span>Sair da Conta</span>}
          </Button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header */}
        <header className="h-16 border-b border-border bg-card/60 backdrop-blur sticky top-0 z-30 px-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-base font-bold tracking-tight capitalize">
              {navItems.find((n) => n.id === activeModule)?.label || "Dashboard"}
            </h1>

            {/* Active Company Selector Button in Header */}
            {activeCompany && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsCompanyModalOpen(true)}
                className="hidden sm:flex items-center gap-2 h-8 text-xs font-semibold border-border/80"
              >
                <Building2 className="h-3.5 w-3.5 text-emerald-500" />
                <span className="max-w-[160px] truncate">{activeCompany.name}</span>
                <ChevronDown className="h-3 w-3 text-muted-foreground" />
              </Button>
            )}
          </div>

          {/* Right Status & Profile Controls */}
          <div className="flex items-center gap-3">
            {syncStats.syncingCount > 0 ? (
              <Badge
                variant="outline"
                onClick={() => setIsSyncModalOpen(true)}
                className="gap-1.5 px-2.5 py-1 text-xs font-medium border-blue-500/40 text-blue-500 bg-blue-500/10 cursor-pointer hover:bg-blue-500/20 transition-colors animate-pulse"
                title="Clique para abrir central de sincronização"
              >
                <RefreshCw className="h-3 w-3 animate-spin" /> Sincronizando ({syncStats.pendingCount})
              </Badge>
            ) : syncStats.pendingCount > 0 ? (
              <Badge
                variant="outline"
                onClick={() => setIsSyncModalOpen(true)}
                className="gap-1.5 px-2.5 py-1 text-xs font-medium border-amber-500/40 text-amber-500 bg-amber-500/10 cursor-pointer hover:bg-amber-500/20 transition-colors"
                title="Clique para abrir central de sincronização"
              >
                <AlertCircle className="h-3 w-3" /> Pendente ({syncStats.pendingCount})
              </Badge>
            ) : syncStats.isOnline ? (
              <Badge
                variant="success"
                onClick={() => setIsSyncModalOpen(true)}
                className="gap-1.5 px-2.5 py-1 text-xs font-medium cursor-pointer hover:opacity-90 transition-opacity"
                title="Clique para abrir central de sincronização"
              >
                <Wifi className="h-3 w-3" /> Cloud Conectado
              </Badge>
            ) : (
              <Badge
                variant="destructive"
                onClick={() => setIsSyncModalOpen(true)}
                className="gap-1.5 px-2.5 py-1 text-xs font-medium cursor-pointer hover:opacity-90 transition-opacity"
                title="Clique para abrir central de sincronização"
              >
                <WifiOff className="h-3 w-3" /> Modo Offline (SQLite)
              </Badge>
            )}

            <Button
              variant="outline"
              size="icon"
              onClick={toggleTheme}
              className="h-9 w-9"
              title={`Alternar para tema ${theme === "light" ? "escuro" : "claro"}`}
            >
              {theme === "light" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4 text-amber-400" />}
            </Button>

            {/* User Profile Badge */}
            {user && (
              <div className="flex items-center gap-2 pl-2 border-l border-border">
                <div className="h-8 w-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-xs border border-primary/20">
                  {user.name.charAt(0).toUpperCase()}
                </div>
                <div className="hidden lg:flex flex-col text-left">
                  <span className="text-xs font-semibold leading-tight truncate max-w-[140px]">
                    {user.name}
                  </span>
                  <span className="text-[10px] text-muted-foreground leading-tight truncate">
                    {user.is_superuser ? "Super Admin" : user.email}
                  </span>
                </div>
              </div>
            )}
          </div>
        </header>

        {/* Dynamic Page Content */}
        <main className="flex-1 p-6 overflow-y-auto">{children}</main>
      </div>

      {/* Modal de Seleção de Empresa */}
      <CompanySelectorModal
        isOpen={isCompanyModalOpen}
        onClose={() => setIsCompanyModalOpen(false)}
      />

      {/* Modal de Status de Sincronização Local-First */}
      <SyncStatusModal
        isOpen={isSyncModalOpen}
        onClose={() => setIsSyncModalOpen(false)}
      />

      {/* Banner / Modal de Atualização Automática */}
      <UpdateModal
        isOpen={isUpdateModalOpen}
        onClose={() => setIsUpdateModalOpen(false)}
        updateData={updateData}
      />
    </div>
  );
}

