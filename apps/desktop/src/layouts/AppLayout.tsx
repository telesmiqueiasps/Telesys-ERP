import React, { useState } from "react";
import {
  Layers,
  LayoutDashboard,
  ShoppingCart,
  Package,
  DollarSign,
  Users,
  Settings,
  LogOut,
  Building2,
  ChevronLeft,
  ChevronRight,
  Sun,
  Moon,
  Wifi,
  ChevronDown,
} from "lucide-react";
import { useAuthStore } from "@/store/useAuthStore";
import { useAppStore } from "@/store/useAppStore";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CompanySelectorModal } from "@/components/CompanySelectorModal";

interface AppLayoutProps {
  children: React.ReactNode;
  activeModule?: string;
  onNavigate?: (module: string) => void;
}

export function AppLayout({ children, activeModule = "dashboard", onNavigate }: AppLayoutProps) {
  const { user, activeCompany, logout } = useAuthStore();
  const { theme, toggleTheme, isSidebarOpen, toggleSidebar } = useAppStore();
  const [isCompanyModalOpen, setIsCompanyModalOpen] = useState(false);

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "pdv", label: "PDV (Frente de Caixa)", icon: ShoppingCart },
    { id: "estoque", label: "Estoque & Produtos", icon: Package },
    { id: "financeiro", label: "Financeiro & Caixa", icon: DollarSign },
    { id: "cadastros", label: "Cadastros & Clientes", icon: Users },
    { id: "configuracoes", label: "Configurações", icon: Settings },
  ];

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
            <Badge variant="success" className="gap-1 px-2.5 py-0.5 text-xs font-medium">
              <Wifi className="h-3 w-3" /> API Cloud Conectada
            </Badge>

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
    </div>
  );
}
