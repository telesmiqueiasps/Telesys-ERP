import { useState, useEffect } from "react";
import { useAuthStore } from "@/store/useAuthStore";
import { LoginView } from "@/pages/LoginView";
import { AppLayout } from "@/layouts/AppLayout";
import { DashboardView } from "@/pages/DashboardView";
import { ProductsView } from "@/pages/ProductsView";
import { PurchasesView } from "@/pages/PurchasesView";
import { CustomersView } from "@/pages/CustomersView";
import { FinanceView } from "@/pages/FinanceView";
import { CashView } from "@/pages/CashView";
import { AuditView } from "@/pages/AuditView";
import { PdvView } from "@/pages/PdvView";
import { SettingsView } from "@/pages/SettingsView";
import { SuperAdminView } from "@/pages/SuperAdminView";
import { ReportsView } from "@/pages/ReportsView";
import { UpdateModal } from "@/components/UpdateModal";
import { updaterService } from "@/services/updaterService";
import { UpdateCheckResponse } from "@/types/updater";

export function App() {
  const { isAuthenticated } = useAuthStore();
  const [activeModule, setActiveModule] = useState<string>("dashboard");
  const [updateData, setUpdateData] = useState<UpdateCheckResponse | null>(null);
  const [isUpdateModalOpen, setIsUpdateModalOpen] = useState(false);

  useEffect(() => {
    // Check silencioso de atualização do aplicativo no início (antes/depois de logar)
    updaterService.checkForUpdates()
      .then((data) => {
        if (data.update_available) {
          setUpdateData(data);
          setIsUpdateModalOpen(true);
        }
      })
      .catch(() => {});
  }, []);

  const renderModuleContent = () => {
    switch (activeModule) {
      case "dashboard":
        return <DashboardView onNavigate={setActiveModule} />;
      case "pdv":
        return <PdvView />;
      case "caixa":
        return <CashView />;
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
    <>
      {!isAuthenticated ? (
        <LoginView />
      ) : (
        <AppLayout activeModule={activeModule} onNavigate={setActiveModule}>
          {renderModuleContent()}
        </AppLayout>
      )}

      {/* Banner / Modal de Atualização Automática Globais */}
      <UpdateModal
        isOpen={isUpdateModalOpen}
        onClose={() => setIsUpdateModalOpen(false)}
        updateData={updateData}
      />
    </>
  );
}
