import { useState } from "react";
import { Building2, Check } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuthStore, CompanyInfo } from "@/store/useAuthStore";
import { localDbManager } from "@/services/localDb/databaseManager";
import { getCompanyDbName } from "@/services/localDb/config";

interface CompanySelectorModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CompanySelectorModal({ isOpen, onClose }: CompanySelectorModalProps) {
  const { user, activeCompany, setActiveCompany } = useAuthStore();
  const [selectedId, setSelectedId] = useState<string>(activeCompany?.id || (user?.companies?.[0]?.id || ""));

  if (!isOpen || !user) return null;

  const handleSelectCompany = async (company: CompanyInfo) => {
    setSelectedId(company.id);

    // 1. Open SQLite database for the selected company
    await localDbManager.openCompanyDatabase(company.id);

    // 2. Set active company in global Zustand store
    setActiveCompany(company);

    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in-50">
      <Card className="w-full max-w-lg border-border/80 shadow-2xl bg-card overflow-hidden">
        <CardHeader className="bg-muted/40 border-b border-border pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="h-9 w-9 rounded-lg bg-primary/10 text-primary flex items-center justify-center font-bold">
                <Building2 className="h-5 w-5" />
              </div>
              <div>
                <CardTitle className="text-lg font-bold tracking-tight">Seleção de Empresa</CardTitle>
                <CardDescription className="text-xs">
                  Selecione qual empresa/CNPJ deseja carregar para a operação local
                </CardDescription>
              </div>
            </div>
            {user.tenant && (
              <Badge variant="outline" className="text-xs font-normal">
                {user.tenant.name}
              </Badge>
            )}
          </div>
        </CardHeader>

        <CardContent className="p-6 space-y-4">
          <div className="space-y-2">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Empresas Autorizadas ({user.companies?.length || 0})
            </label>

            <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
              {user.companies && user.companies.length > 0 ? (
                user.companies.map((company) => {
                  const isSelected = selectedId === company.id;
                  const dbName = getCompanyDbName(company.id);

                  return (
                    <div
                      key={company.id}
                      onClick={() => handleSelectCompany(company)}
                      className={`p-4 rounded-xl border transition-all duration-150 cursor-pointer flex items-center justify-between ${
                        isSelected
                          ? "border-primary bg-primary/5 shadow-sm ring-1 ring-primary/30"
                          : "border-border/60 bg-card hover:bg-accent/50 hover:border-border"
                      }`}
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-foreground">{company.name}</span>
                          {company.trade_name && (
                            <span className="text-xs text-muted-foreground">({company.trade_name})</span>
                          )}
                        </div>
                        <div className="flex items-center gap-3 text-xs text-muted-foreground font-mono">
                          <span>CNPJ: {company.cnpj || "Não informado"}</span>
                          <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-sans">
                            • SQLite: {dbName}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {isSelected && (
                          <div className="h-6 w-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center">
                            <Check className="h-3.5 w-3.5" />
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="p-6 text-center text-xs text-muted-foreground border border-dashed rounded-xl">
                  Nenhuma empresa cadastrada para este Tenant.
                </div>
              )}
            </div>
          </div>

          <div className="pt-2 flex justify-end gap-2 border-t">
            <Button
              variant="outline"
              size="sm"
              onClick={onClose}
              className="text-xs"
            >
              Cancelar
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
