import { useState } from "react";
import { useAuthStore } from "@/store/useAuthStore";
import { LoginView } from "@/pages/LoginView";
import { AppLayout } from "@/layouts/AppLayout";
import { DashboardView } from "@/pages/DashboardView";
import { ProductsView } from "@/pages/ProductsView";
import { PurchasesView } from "@/pages/PurchasesView";
import { CustomersView } from "@/pages/CustomersView";
import { FinanceView } from "@/pages/FinanceView";
import { AuditView } from "@/pages/AuditView";
import { PdvView } from "@/pages/PdvView";
import { SettingsView } from "@/pages/SettingsView";
import { SuperAdminView } from "@/pages/SuperAdminView";
import { ReportsView } from "@/pages/ReportsView";

export function App() {
  const { isAuthenticated } = useAuthStore();
  const [activeModule, setActiveModule] = useState<string>("dashboard");

  if (!isAuthenticated) {
    return <LoginView />;
  }

  const renderModuleContent = () => {
    switch (activeModule) {
      case "dashboard":
        return <DashboardView onNavigate={setActiveModule} />;
      case "pdv":
        return <PdvView />;
      case "estoque":
        return <ProductsView />;
      case "compras":
        return <PurchasesView />;
      case "cadastros":
        return <CustomersView />;
      case "financeiro":
        return <FinanceView />;
      case "relatorios":
        return <ReportsView />;
      case "auditoria":
        return <AuditView />;
      case "configuracoes":
        return <SettingsView />;
      case "superadmin":
        return <SuperAdminView />;
      default:
        return <DashboardView onNavigate={setActiveModule} />;
    }
  };



  return (
    <AppLayout activeModule={activeModule} onNavigate={setActiveModule}>
      {renderModuleContent()}
    </AppLayout>
  );
}
