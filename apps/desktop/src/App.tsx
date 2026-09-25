import { useState } from "react";
import { useAuthStore } from "@/store/useAuthStore";
import { LoginView } from "@/pages/LoginView";
import { AppLayout } from "@/layouts/AppLayout";
import { DashboardView } from "@/pages/DashboardView";
import { ProductsView } from "@/pages/ProductsView";
import { CustomersView } from "@/pages/CustomersView";
import { CashView } from "@/pages/CashView";
import { PdvView } from "@/pages/PdvView";

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
      case "cadastros":
        return <CustomersView />;
      case "financeiro":
        return <CashView />;
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
