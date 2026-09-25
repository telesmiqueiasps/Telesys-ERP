import { useQuery } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Layers,
  Server,
  Database,
  Monitor,
  Moon,
  Sun,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Cpu,
  FileCode2,
  Box
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import { useAppStore } from "@/store/useAppStore";

const ConnectionTestSchema = z.object({
  apiEndpoint: z.string().url("Informe uma URL válida (ex: http://localhost:8000)")
});

type ConnectionTestForm = z.infer<typeof ConnectionTestSchema>;

export function App() {
  const { theme, toggleTheme } = useAppStore();

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors }
  } = useForm<ConnectionTestForm>({
    resolver: zodResolver(ConnectionTestSchema),
    defaultValues: {
      apiEndpoint: import.meta.env.VITE_API_URL || "http://localhost:8000"
    }
  });

  const currentEndpoint = watch("apiEndpoint");

  // TanStack Query configured to check API Health endpoint
  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["healthCheck", currentEndpoint],
    queryFn: async () => {
      const response = await fetch(`${currentEndpoint}/api/v1/health`, {
        headers: { Accept: "application/json" }
      });
      if (!response.ok) {
        throw new Error(`Status de erro HTTP: ${response.status}`);
      }
      return response.json();
    },
    retry: 1,
    staleTime: 10000
  });

  const onSubmit = () => {
    refetch();
  };

  return (
    <div className="min-h-screen bg-background text-foreground transition-colors duration-200">
      {/* Top Header */}
      <header className="border-b bg-card/60 backdrop-blur sticky top-0 z-50">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-primary/10 text-primary flex items-center justify-center font-bold">
              <Layers className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight">Telesys ERP</h1>
              <p className="text-xs text-muted-foreground">Fundação do Monorepo</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="icon"
              onClick={toggleTheme}
              title={`Alternar para modo ${theme === "light" ? "escuro" : "claro"}`}
            >
              {theme === "light" ? (
                <Moon className="h-4 w-4" />
              ) : (
                <Sun className="h-4 w-4 text-amber-400" />
              )}
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8 max-w-6xl space-y-8">
        {/* Banner Status */}
        <section className="rounded-xl border bg-gradient-to-r from-primary/10 via-primary/5 to-transparent p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Ambiente de Fundação Inicializado
            </div>
            <h2 className="text-2xl font-bold">Estrutura Base Pronta para Desenvolvimento</h2>
            <p className="text-sm text-muted-foreground">
              Arquitetura em monorepo configurada com Tauri v2, React, TypeScript, FastAPI, SQLAlchemy 2 e Docker PostgreSQL.
            </p>
          </div>
        </section>

        {/* Stack Verification Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: Desktop Shell */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-base font-semibold">Desktop (Tauri + React)</CardTitle>
              <Monitor className="h-5 w-5 text-primary" />
            </CardHeader>
            <CardContent className="space-y-3">
              <CardDescription>
                Tauri v2 + Vite + React + TypeScript com Tailwind CSS e shadcn/ui.
              </CardDescription>
              <div className="space-y-1.5 text-xs text-muted-foreground">
                <div className="flex items-center justify-between">
                  <span>Gerenciador de Estado</span>
                  <span className="font-mono text-foreground font-medium">Zustand 5</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Data Fetching & Cache</span>
                  <span className="font-mono text-foreground font-medium">TanStack Query 5</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Formulários & Schemas</span>
                  <span className="font-mono text-foreground font-medium">Hook Form + Zod</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Card 2: Backend API */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-base font-semibold">Backend (FastAPI)</CardTitle>
              <Server className="h-5 w-5 text-indigo-500" />
            </CardHeader>
            <CardContent className="space-y-3">
              <CardDescription>
                Python 3.12 + FastAPI assíncrono com SQLAlchemy 2 e Alembic.
              </CardDescription>
              <div className="space-y-1.5 text-xs text-muted-foreground">
                <div className="flex items-center justify-between">
                  <span>ORM & Migrações</span>
                  <span className="font-mono text-foreground font-medium">SQLAlchemy 2 + Alembic</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Validação Python</span>
                  <span className="font-mono text-foreground font-medium">Pydantic v2</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Arquitetura</span>
                  <span className="font-mono text-foreground font-medium">REST API Modular</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Card 3: Database & Infra */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-base font-semibold">PostgreSQL & Infra</CardTitle>
              <Database className="h-5 w-5 text-cyan-500" />
            </CardHeader>
            <CardContent className="space-y-3">
              <CardDescription>
                PostgreSQL conteinerizado via Docker Compose com volume persistente.
              </CardDescription>
              <div className="space-y-1.5 text-xs text-muted-foreground">
                <div className="flex items-center justify-between">
                  <span>Docker Compose</span>
                  <span className="font-mono text-foreground font-medium">PostgreSQL 16 Alpine</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Extensões</span>
                  <span className="font-mono text-foreground font-medium">uuid-ossp, pgcrypto</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Isolamento</span>
                  <span className="font-mono text-foreground font-medium">Ambiente Dev Local</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* API Health & Connection Checker (React Hook Form + Zod + TanStack Query) */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Cpu className="h-5 w-5 text-primary" />
              Verificador de Conectividade do Sistema
            </CardTitle>
            <CardDescription>
              Validação em tempo real utilizando React Hook Form, Zod e TanStack Query conectando ao endpoint de saúde da API.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="flex-1">
                  <input
                    {...register("apiEndpoint")}
                    type="text"
                    placeholder="http://localhost:8000"
                    className="w-full h-10 px-3 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                  {errors.apiEndpoint && (
                    <p className="text-xs text-destructive mt-1">
                      {errors.apiEndpoint.message}
                    </p>
                  )}
                </div>
                <Button type="submit" disabled={isFetching} className="gap-2">
                  <RefreshCw className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
                  Testar Conexão
                </Button>
              </div>
            </form>

            <div className="rounded-lg border p-4 bg-muted/30">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Status da Conexão com a API
                </span>
                {isLoading || isFetching ? (
                  <span className="inline-flex items-center gap-1.5 text-xs text-amber-500 font-medium">
                    <RefreshCw className="h-3.5 w-3.5 animate-spin" /> Verificando...
                  </span>
                ) : isError ? (
                  <span className="inline-flex items-center gap-1.5 text-xs text-destructive font-medium">
                    <AlertCircle className="h-3.5 w-3.5" /> Desconectado / Offline
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                    <CheckCircle2 className="h-3.5 w-3.5" /> Conectado com Sucesso
                  </span>
                )}
              </div>

              {isError && (
                <div className="text-xs text-muted-foreground space-y-1">
                  <p>A API ainda não está rodando nesta porta ou não respondeu.</p>
                  <p className="font-mono bg-muted p-2 rounded">
                    Execute no terminal da API: <span className="text-foreground">uvicorn app.main:app --reload</span>
                  </p>
                </div>
              )}

              {data && (
                <pre className="text-xs font-mono bg-background p-3 rounded border overflow-x-auto text-emerald-600 dark:text-emerald-400">
                  {JSON.stringify(data, null, 2)}
                </pre>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Directory & Monorepo Packages Section */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Box className="h-5 w-5 text-primary" />
              Pacotes Compartilhados do Monorepo
            </CardTitle>
            <CardDescription>
              Módulos isolados configurados no monorepo para reutilização entre Desktop, Web e futuras aplicações.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-lg border bg-card/50 space-y-1.5">
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <FileCode2 className="h-4 w-4 text-primary" />
                  @telesys/shared-types
                </div>
                <p className="text-xs text-muted-foreground">
                  Contratos TypeScript compartilhados para respostas HTTP, paginação e metadados.
                </p>
              </div>

              <div className="p-4 rounded-lg border bg-card/50 space-y-1.5">
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <FileCode2 className="h-4 w-4 text-indigo-500" />
                  @telesys/validation
                </div>
                <p className="text-xs text-muted-foreground">
                  Schemas de validação agnósticos com Zod para requisições e formulários.
                </p>
              </div>

              <div className="p-4 rounded-lg border bg-card/50 space-y-1.5">
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <FileCode2 className="h-4 w-4 text-emerald-500" />
                  @telesys/ui
                </div>
                <p className="text-xs text-muted-foreground">
                  Biblioteca de utilitários de interface, design tokens e ícones Lucide.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}

export default App;
