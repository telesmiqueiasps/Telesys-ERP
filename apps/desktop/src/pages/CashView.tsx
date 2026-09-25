import { useState, useEffect, useCallback } from "react";
import {
  DollarSign,
  Lock,
  Unlock,
  ArrowDownRight,
  ArrowUpRight,
  Plus,
  RefreshCw,
  Clock,
  History,
  AlertTriangle,
  Receipt,
  UserCheck,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CashRegisterDetail, CashMovement } from "@/types/cash";
import { cashService } from "@/services/cashService";
import { useAuthStore } from "@/store/useAuthStore";
import { OpenCashModal } from "@/components/OpenCashModal";
import { CashMovementModal } from "@/components/CashMovementModal";
import { CloseCashModal } from "@/components/CloseCashModal";

export function CashView() {
  const { activeCompany } = useAuthStore();

  const [currentCash, setCurrentCash] = useState<CashRegisterDetail | null>(null);
  const [cashHistory, setCashHistory] = useState<CashRegisterDetail[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"current" | "history">("current");

  // Modals state
  const [isOpenModalOpen, setIsOpenModalOpen] = useState(false);
  const [isCloseModalOpen, setIsCloseModalOpen] = useState(false);
  const [movementModalState, setMovementModalState] = useState<{
    isOpen: boolean;
    type: "SUPPLY" | "BLEED";
  }>({
    isOpen: false,
    type: "SUPPLY",
  });

  const fetchCashData = useCallback(async () => {
    if (!activeCompany) return;
    setLoading(true);
    try {
      const [current, history] = await Promise.all([
        cashService.getCurrentCash(activeCompany.id),
        cashService.getCashHistory(activeCompany.id),
      ]);
      setCurrentCash(current);
      setCashHistory(history);
    } catch (err) {
      console.error("Erro ao carregar dados do caixa:", err);
    } finally {
      setLoading(false);
    }
  }, [activeCompany]);

  useEffect(() => {
    fetchCashData();
  }, [fetchCashData]);

  // Calculate totals for active session
  const initialBalance = currentCash?.initial_balance || 0;
  const currentBalance = currentCash?.current_balance || 0;

  const suppliesTotal =
    currentCash?.movements
      ?.filter((m) => m.movement_type === "SUPPLY")
      .reduce((acc, m) => acc + Number(m.amount), 0) || 0;

  const bleedsTotal =
    currentCash?.movements
      ?.filter((m) => m.movement_type === "BLEED")
      .reduce((acc, m) => acc + Number(m.amount), 0) || 0;

  const salesTotal =
    currentCash?.movements
      ?.filter((m) => m.movement_type === "SALE")
      .reduce((acc, m) => acc + Number(m.amount), 0) || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-emerald-500/10 text-emerald-500 flex items-center justify-center font-bold">
              <DollarSign className="h-5 w-5" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight">Caixa & Gestão Financeira</h1>
          </div>
          <p className="text-sm text-muted-foreground">
            Controle de sessões de caixa do operador, sangrias, suprimentos e conferência de fechamento.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchCashData}
            className="gap-2 text-xs"
            disabled={loading}
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} /> Atualizar
          </Button>

          {currentCash ? (
            <Button
              variant="destructive"
              onClick={() => setIsCloseModalOpen(true)}
              className="gap-2 font-semibold shadow-sm text-xs"
            >
              <Lock className="h-4 w-4" /> Fechar Caixa
            </Button>
          ) : (
            <Button
              onClick={() => setIsOpenModalOpen(true)}
              className="gap-2 font-semibold shadow-sm bg-emerald-600 hover:bg-emerald-700 text-xs"
            >
              <Unlock className="h-4 w-4" /> Abrir Novo Caixa
            </Button>
          )}
        </div>
      </div>

      {/* Main Cash Status Hero Banner */}
      <Card className="p-6 border-border/60 shadow-sm relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          {/* Status badge & info */}
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              {currentCash ? (
                <Badge variant="success" className="gap-1.5 px-3 py-1 text-xs font-bold uppercase tracking-wider">
                  <Unlock className="h-3.5 w-3.5" /> Caixa Aberto
                </Badge>
              ) : (
                <Badge variant="secondary" className="gap-1.5 px-3 py-1 text-xs font-bold uppercase tracking-wider bg-amber-500/10 text-amber-500 border-amber-500/20">
                  <Lock className="h-3.5 w-3.5" /> Caixa Fechado
                </Badge>
              )}

              {currentCash?.opened_at && (
                <span className="text-xs text-muted-foreground flex items-center gap-1 font-medium">
                  <Clock className="h-3.5 w-3.5" /> Aberto em:{" "}
                  {new Date(currentCash.opened_at).toLocaleString("pt-BR")}
                </span>
              )}
            </div>

            <div>
              <span className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">
                Saldo Atual Disponível no Caixa
              </span>
              <div className="text-3xl font-extrabold tracking-tight font-mono text-foreground mt-0.5">
                R${" "}
                {currentBalance.toLocaleString("pt-BR", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </div>
            </div>

            {currentCash?.user_name && (
              <div className="text-xs text-muted-foreground flex items-center gap-1.5 pt-1">
                <UserCheck className="h-3.5 w-3.5 text-primary" /> Operador responsável:{" "}
                <span className="font-semibold text-foreground">{currentCash.user_name}</span>
              </div>
            )}
          </div>

          {/* Quick Actions (if open) or Open button (if closed) */}
          {currentCash ? (
            <div className="flex flex-wrap items-center gap-3">
              <Button
                onClick={() => setMovementModalState({ isOpen: true, type: "SUPPLY" })}
                className="gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs h-10 px-4"
              >
                <ArrowDownRight className="h-4 w-4" /> + Suprimento
              </Button>
              <Button
                onClick={() => setMovementModalState({ isOpen: true, type: "BLEED" })}
                variant="outline"
                className="gap-2 border-amber-500/40 text-amber-500 hover:bg-amber-500/10 font-semibold text-xs h-10 px-4"
              >
                <ArrowUpRight className="h-4 w-4" /> - Sangria
              </Button>
            </div>
          ) : (
            <div>
              <Button
                onClick={() => setIsOpenModalOpen(true)}
                className="gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm h-11 px-6 shadow-md"
              >
                <Unlock className="h-4 w-4" /> Abrir Caixa Agora
              </Button>
            </div>
          )}
        </div>
      </Card>

      {/* Summary Cards Grid (Only visible if cash is open) */}
      {currentCash && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="p-4 border-border/60 shadow-sm space-y-1">
            <span className="text-xs font-semibold text-muted-foreground uppercase">Fundo de Abertura</span>
            <div className="text-xl font-bold font-mono text-foreground">
              R$ {initialBalance.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
            </div>
            <p className="text-[11px] text-muted-foreground">Troco inicial declarado na abertura</p>
          </Card>

          <Card className="p-4 border-border/60 shadow-sm space-y-1">
            <span className="text-xs font-semibold text-muted-foreground uppercase flex items-center gap-1">
              <ArrowDownRight className="h-3.5 w-3.5 text-emerald-500" /> Suprimentos (+)
            </span>
            <div className="text-xl font-bold font-mono text-emerald-500">
              R$ {suppliesTotal.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
            </div>
            <p className="text-[11px] text-muted-foreground">Entradas manuais de dinheiro</p>
          </Card>

          <Card className="p-4 border-border/60 shadow-sm space-y-1">
            <span className="text-xs font-semibold text-muted-foreground uppercase flex items-center gap-1">
              <ArrowUpRight className="h-3.5 w-3.5 text-amber-500" /> Sangrias (-)
            </span>
            <div className="text-xl font-bold font-mono text-amber-500">
              R$ {bleedsTotal.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
            </div>
            <p className="text-[11px] text-muted-foreground">Retiradas efetuadas do caixa</p>
          </Card>

          <Card className="p-4 border-border/60 shadow-sm space-y-1">
            <span className="text-xs font-semibold text-muted-foreground uppercase flex items-center gap-1">
              <Receipt className="h-3.5 w-3.5 text-primary" /> Vendas PDV
            </span>
            <div className="text-xl font-bold font-mono text-primary">
              R$ {salesTotal.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
            </div>
            <p className="text-[11px] text-muted-foreground">Total em vendas registradas</p>
          </Card>
        </div>
      )}

      {/* Tabs: Movimentações da Sessão Atual / Histórico de Caixas */}
      <Card className="p-4 border-border/60 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-border/60 pb-3">
          <div className="flex items-center p-1 bg-muted/60 rounded-xl border border-border/40">
            <button
              onClick={() => setActiveTab("current")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                activeTab === "current"
                  ? "bg-card text-foreground shadow-sm border border-border/40"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Receipt className="h-4 w-4 text-primary" /> Movimentações da Sessão Atual
            </button>
            <button
              onClick={() => setActiveTab("history")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                activeTab === "history"
                  ? "bg-card text-foreground shadow-sm border border-border/40"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <History className="h-4 w-4 text-primary" /> Histórico de Caixas Encerrados
            </button>
          </div>
        </div>

        {/* Tab 1: Current Session Movements */}
        {activeTab === "current" && (
          <div>
            {!currentCash ? (
              <div className="p-8 text-center space-y-3">
                <Lock className="h-8 w-8 text-muted-foreground/50 mx-auto" />
                <p className="text-sm font-medium text-muted-foreground">
                  Nenhuma sessão de caixa aberta no momento.
                </p>
                <Button
                  size="sm"
                  onClick={() => setIsOpenModalOpen(true)}
                  className="gap-2 bg-emerald-600 hover:bg-emerald-700 text-xs font-semibold"
                >
                  <Plus className="h-3.5 w-3.5" /> Abrir Caixa para Ver Movimentos
                </Button>
              </div>
            ) : currentCash.movements.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground text-sm">
                Nenhuma movimentação registrada nesta sessão.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-muted/40 border-b border-border text-muted-foreground text-xs font-semibold uppercase tracking-wider">
                    <tr>
                      <th className="py-3 px-4">Horário</th>
                      <th className="py-3 px-4">Tipo</th>
                      <th className="py-3 px-4">Forma de Pgto</th>
                      <th className="py-3 px-4">Descrição</th>
                      <th className="py-3 px-4 text-right">Valor (R$)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/60">
                    {currentCash.movements.map((mov: CashMovement) => {
                      const isPositive =
                        mov.movement_type === "OPENING" ||
                        mov.movement_type === "SUPPLY" ||
                        mov.movement_type === "SALE";
                      return (
                        <tr key={mov.id} className="hover:bg-muted/30 transition-colors">
                          <td className="py-3 px-4 text-xs font-mono text-muted-foreground">
                            {new Date(mov.created_at).toLocaleTimeString("pt-BR")}
                          </td>
                          <td className="py-3 px-4">
                            {mov.movement_type === "OPENING" && (
                              <Badge variant="outline" className="text-xs bg-blue-500/10 text-blue-500 border-blue-500/20">
                                Abertura
                              </Badge>
                            )}
                            {mov.movement_type === "SUPPLY" && (
                              <Badge variant="success" className="text-xs">
                                Suprimento
                              </Badge>
                            )}
                            {mov.movement_type === "BLEED" && (
                              <Badge variant="secondary" className="text-xs bg-amber-500/10 text-amber-500 border-amber-500/20">
                                Sangria
                              </Badge>
                            )}
                            {mov.movement_type === "CLOSING" && (
                              <Badge variant="destructive" className="text-xs">
                                Fechamento
                              </Badge>
                            )}
                            {mov.movement_type === "SALE" && (
                              <Badge variant="outline" className="text-xs bg-emerald-500/10 text-emerald-500 border-emerald-500/20">
                                Venda PDV
                              </Badge>
                            )}
                          </td>
                          <td className="py-3 px-4 text-xs font-medium">
                            {mov.payment_method === "MONEY" ? "Dinheiro" : mov.payment_method}
                          </td>
                          <td className="py-3 px-4 text-xs text-muted-foreground">
                            {mov.description || "-"}
                          </td>
                          <td
                            className={`py-3 px-4 text-right font-mono font-bold text-xs ${
                              isPositive ? "text-emerald-500" : "text-amber-500"
                            }`}
                          >
                            {isPositive ? "+" : "-"} R${" "}
                            {Number(mov.amount).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: History of Closed Cash Sessions */}
        {activeTab === "history" && (
          <div>
            {cashHistory.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground text-sm">
                Nenhum histórico de caixa encerrado encontrado.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-muted/40 border-b border-border text-muted-foreground text-xs font-semibold uppercase tracking-wider">
                    <tr>
                      <th className="py-3 px-4">Operador</th>
                      <th className="py-3 px-4">Abertura / Fechamento</th>
                      <th className="py-3 px-4">Fundo Inicial</th>
                      <th className="py-3 px-4">Saldo Apurado</th>
                      <th className="py-3 px-4">Saldo Declarado</th>
                      <th className="py-3 px-4">Divergência</th>
                      <th className="py-3 px-4">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/60">
                    {cashHistory.map((reg) => {
                      const diff = reg.difference_amount || 0;
                      return (
                        <tr key={reg.id} className="hover:bg-muted/30 transition-colors">
                          <td className="py-3 px-4 font-semibold text-xs">
                            {reg.user_name || "Operador"}
                          </td>
                          <td className="py-3 px-4 text-xs text-muted-foreground space-y-0.5">
                            <div>
                              Ab: {new Date(reg.opened_at).toLocaleString("pt-BR")}
                            </div>
                            {reg.closed_at && (
                              <div className="text-[11px]">
                                Fe: {new Date(reg.closed_at).toLocaleString("pt-BR")}
                              </div>
                            )}
                          </td>
                          <td className="py-3 px-4 font-mono text-xs">
                            R$ {Number(reg.initial_balance).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                          </td>
                          <td className="py-3 px-4 font-mono text-xs">
                            R$ {Number(reg.current_balance).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                          </td>
                          <td className="py-3 px-4 font-mono text-xs">
                            {reg.final_declared_balance != null
                              ? `R$ ${Number(reg.final_declared_balance).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`
                              : "-"}
                          </td>
                          <td className="py-3 px-4">
                            {reg.status === "CLOSED" ? (
                              <span
                                className={`font-mono text-xs font-bold flex items-center gap-1 ${
                                  diff === 0
                                    ? "text-emerald-500"
                                    : diff > 0
                                    ? "text-blue-500"
                                    : "text-amber-500"
                                }`}
                              >
                                {diff !== 0 && <AlertTriangle className="h-3 w-3" />}
                                {diff > 0 ? "+" : ""} R${" "}
                                {Number(diff).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                              </span>
                            ) : (
                              "-"
                            )}
                          </td>
                          <td className="py-3 px-4">
                            {reg.status === "OPEN" ? (
                              <Badge variant="success" className="text-[11px]">
                                Aberto
                              </Badge>
                            ) : (
                              <Badge variant="secondary" className="text-[11px]">
                                Fechado
                              </Badge>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Modals */}
      <OpenCashModal
        isOpen={isOpenModalOpen}
        onClose={() => setIsOpenModalOpen(false)}
        onSuccess={fetchCashData}
      />

      <CashMovementModal
        isOpen={movementModalState.isOpen}
        type={movementModalState.type}
        onClose={() => setMovementModalState({ ...movementModalState, isOpen: false })}
        onSuccess={fetchCashData}
      />

      <CloseCashModal
        isOpen={isCloseModalOpen}
        currentCash={currentCash}
        onClose={() => setIsCloseModalOpen(false)}
        onSuccess={fetchCashData}
      />
    </div>
  );
}
