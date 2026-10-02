import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Lock,
  Mail,
  Eye,
  EyeOff,
  ArrowRight,
  ShieldCheck,
  Zap,
  AlertCircle,
  Loader2,
  Sparkles,
  Moon,
  Sun,
  UserCheck,
  Building2,
  KeyRound,
  ArrowLeft,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiFetch } from "@/lib/apiClient";
import { useAuthStore, UserMe } from "@/store/useAuthStore";
import { useAppStore } from "@/store/useAppStore";
import logoImg from "@/assets/logo.png";

const LoginSchema = z.object({
  email: z.string().min(1, "Informe o e-mail").email("Informe um e-mail válido"),
  password: z.string().min(1, "Informe a senha"),
});

type LoginFormValues = z.infer<typeof LoginSchema>;

interface QuickUser {
  id: string;
  name: string;
  email: string;
  role_name?: string;
  is_active: boolean;
}

export function LoginView() {
  const { setSession } = useAuthStore();
  const { theme, toggleTheme } = useAppStore();
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Card-based Quick Login state
  const [loginMode, setLoginMode] = useState<"cards" | "manual">("cards");
  const [quickUsers, setQuickUsers] = useState<QuickUser[]>([]);
  const [selectedUser, setSelectedUser] = useState<QuickUser | null>(null);
  const [loadingQuickUsers, setLoadingQuickUsers] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(LoginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  // Fetch quick users on mount
  useEffect(() => {
    // Check localStorage cache first for fast local-first render
    const cachedUsersStr = localStorage.getItem("telesys_quick_users_cache");
    if (cachedUsersStr) {
      try {
        setQuickUsers(JSON.parse(cachedUsersStr));
      } catch (e) {}
    }

    setLoadingQuickUsers(true);
    apiFetch<QuickUser[]>("/auth/quick-users")
      .then((data) => {
        if (data && data.length > 0) {
          setQuickUsers(data);
          localStorage.setItem("telesys_quick_users_cache", JSON.stringify(data));
        }
      })
      .catch((err) => {
        console.warn("[LoginView] Erro ao buscar usuários rápidos da nuvem, usando cache local:", err);
      })
      .finally(() => {
        setLoadingQuickUsers(false);
      });
  }, []);

  const handleSelectCardUser = (user: QuickUser) => {
    setSelectedUser(user);
    setValue("email", user.email, { shouldValidate: true });
    setValue("password", "", { shouldValidate: false });
    setErrorMessage(null);
  };

  const onSubmit = async (values: LoginFormValues) => {
    setErrorMessage(null);
    setIsSubmitting(true);
    try {
      // 1. Authenticate with Cloud API
      const tokenData = await apiFetch<{
        access_token: string;
        refresh_token: string;
        token_type: string;
      }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email: values.email,
          password: values.password,
        }),
      });

      // 2. Fetch authenticated user profile & permissions
      const userData = await apiFetch<UserMe>("/auth/me", {}, tokenData.access_token);

      // 3. Save session in Auth Store
      setSession(tokenData.access_token, tokenData.refresh_token, userData);
    } catch (err: any) {
      setErrorMessage(err.message || "Falha na autenticação. Verifique suas credenciais.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const getRoleGradient = (roleName?: string) => {
    switch (roleName?.toLowerCase()) {
      case "administrador":
        return "from-amber-500 to-red-600 text-white";
      case "gestor":
        return "from-blue-600 to-indigo-600 text-white";
      case "supervisor":
        return "from-purple-600 to-pink-600 text-white";
      case "operador de caixa":
        return "from-emerald-500 to-teal-600 text-white";
      case "financeiro":
        return "from-cyan-500 to-blue-600 text-white";
      case "estoquista":
        return "from-orange-500 to-amber-600 text-white";
      default:
        return "from-slate-600 to-slate-800 text-white";
    }
  };

  return (
    <div className="min-h-screen flex bg-background text-foreground transition-colors duration-200">
      {/* Left Branding Banner */}
      <div className="hidden lg:flex lg:w-1/2 relative bg-slate-900 text-white flex-col justify-between p-12 overflow-hidden border-r border-slate-800">
        {/* Ambient Gradient Orbs */}
        <div className="absolute -top-24 -left-24 w-96 h-96 bg-primary/30 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl pointer-events-none" />

        {/* Brand Header */}
        <div className="relative z-10 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src={logoImg} alt="Telesys Logo" className="h-12 w-auto object-contain drop-shadow-md" />
          </div>

          <Badge variant="outline" className="border-slate-700 bg-slate-800/60 text-slate-300">
            v0.1.0 Cloud Foundation
          </Badge>
        </div>

        {/* Feature Highlights */}
        <div className="relative z-10 space-y-8 my-auto">
          <div>
            <Badge variant="secondary" className="mb-4 bg-blue-500/10 text-blue-300 border-blue-500/20 gap-1.5 px-3 py-1">
              <Sparkles className="h-3.5 w-3.5 text-blue-400" /> Acesso Rápido por Cards
            </Badge>
            <h2 className="text-3xl font-extrabold tracking-tight leading-tight">
              Agilidade e segurança no acesso diário da sua empresa.
            </h2>
            <p className="mt-3 text-slate-400 text-sm leading-relaxed max-w-md">
              Selecione o operador ou gestor diretamente no card do terminal e informe apenas a senha para entrar no sistema com velocidade ultra-rápida.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4 pt-2">
            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/50 backdrop-blur space-y-2">
              <div className="h-8 w-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
                <Zap className="h-4 w-4" />
              </div>
              <h3 className="text-sm font-semibold text-slate-200">PDV Offline-First</h3>
              <p className="text-xs text-slate-400">Operação contínua de vendas no caixa mesmo sem internet.</p>
            </div>

            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/50 backdrop-blur space-y-2">
              <div className="h-8 w-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center">
                <ShieldCheck className="h-4 w-4" />
              </div>
              <h3 className="text-sm font-semibold text-slate-200">Segurança RBAC</h3>
              <p className="text-xs text-slate-400">Cargos pré-definidos (Gestor, Caixa, Supervisor, Estoquista).</p>
            </div>
          </div>
        </div>

        {/* Footer info */}
        <div className="relative z-10 flex items-center justify-between text-xs text-slate-500 border-t border-slate-800/80 pt-6">
          <span>&copy; 2026 Telesys ERP. Todos os direitos reservados.</span>
          <div className="flex items-center gap-2 text-emerald-400 font-medium">
            <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            Terminal Conectado
          </div>
        </div>
      </div>

      {/* Right Login Form Container */}
      <div className="w-full lg:w-1/2 flex flex-col justify-between p-6 sm:p-12 overflow-y-auto">
        {/* Header Bar */}
        <div className="flex justify-between items-center w-full max-w-lg mx-auto">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center font-bold">
              <Building2 className="h-4 w-4" />
            </div>
            <div className="flex flex-col">
              <span className="font-bold tracking-tight text-xs text-foreground">Telesys ERP Terminal</span>
              <span className="text-[10px] text-muted-foreground">Empresa Matriz Pré-selecionada</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" onClick={toggleTheme} title="Alternar tema">
              {theme === "light" ? <Moon className="h-4 w-4 text-slate-700" /> : <Sun className="h-4 w-4 text-amber-400" />}
            </Button>
          </div>
        </div>

        {/* Center Container */}
        <div className="w-full max-w-lg mx-auto my-auto py-6 space-y-6">
          <Card className="border-border/60 shadow-xl shadow-black/5 backdrop-blur">
            <CardHeader className="space-y-1 pb-4">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xl font-bold tracking-tight">
                  {loginMode === "cards" ? "Selecione seu Usuário" : "Login por E-mail & Senha"}
                </CardTitle>
                <Badge variant="outline" className="text-xs font-normal gap-1 border-primary/30 text-primary">
                  <UserCheck className="h-3 w-3" />
                  {loginMode === "cards" ? "Modo Cards Rápido" : "Modo Manual"}
                </Badge>
              </div>
              <CardDescription className="text-xs">
                {loginMode === "cards"
                  ? "Clique no seu nome/cargo para informar a senha de acesso"
                  : "Informe seu e-mail e senha cadastrados no sistema"}
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              {errorMessage && (
                <div className="p-3.5 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-xs flex items-start gap-2.5 leading-relaxed animate-in fade-in-50">
                  <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                  <span>{errorMessage}</span>
                </div>
              )}

              {/* CARD-BASED LOGIN MODE */}
              {loginMode === "cards" && (
                <div className="space-y-4">
                  {/* Selected User Password Form Modal/Focus */}
                  {selectedUser ? (
                    <div className="p-4 rounded-xl bg-card border-2 border-primary/40 shadow-md space-y-4 animate-in fade-in-50">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div
                            className={`h-10 w-10 rounded-full bg-gradient-to-br ${getRoleGradient(
                              selectedUser.role_name
                            )} flex items-center justify-center font-bold text-sm shadow-sm`}
                          >
                            {selectedUser.name.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="font-bold text-sm text-foreground">{selectedUser.name}</p>
                            <p className="text-xs text-muted-foreground">{selectedUser.email}</p>
                          </div>
                        </div>

                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 text-xs gap-1 text-muted-foreground hover:text-foreground"
                          onClick={() => setSelectedUser(null)}
                        >
                          <ArrowLeft className="h-3.5 w-3.5" /> Trocar
                        </Button>
                      </div>

                      <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
                        <div className="space-y-1.5">
                          <Label htmlFor="password" className="text-xs font-semibold">
                            Senha de Acesso para {selectedUser.name}
                          </Label>
                          <div className="relative">
                            <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                            <Input
                              id="password"
                              type={showPassword ? "text" : "password"}
                              placeholder="Digite sua senha..."
                              className="pl-9 pr-9 h-10"
                              autoFocus
                              {...register("password")}
                            />
                            <button
                              type="button"
                              onClick={() => setShowPassword(!showPassword)}
                              className="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground transition-colors"
                              tabIndex={-1}
                            >
                              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                            </button>
                          </div>
                          {errors.password && (
                            <p className="text-xs text-destructive mt-1">{errors.password.message}</p>
                          )}
                        </div>

                        <Button
                          type="submit"
                          className="w-full h-10 gap-2 font-semibold shadow-md"
                          disabled={isSubmitting}
                        >
                          {isSubmitting ? (
                            <>
                              <Loader2 className="h-4 w-4 animate-spin" /> Autenticando...
                            </>
                          ) : (
                            <>
                              Entrar no Sistema <ArrowRight className="h-4 w-4" />
                            </>
                          )}
                        </Button>
                      </form>
                    </div>
                  ) : (
                    /* User Cards Grid */
                    <div className="space-y-3">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[340px] overflow-y-auto pr-1">
                        {quickUsers.map((u) => (
                          <button
                            key={u.id}
                            type="button"
                            onClick={() => handleSelectCardUser(u)}
                            className="p-3.5 rounded-xl border border-border/80 bg-muted/20 hover:bg-muted/60 hover:border-primary/50 text-left flex items-center gap-3 transition-all duration-200 group hover:shadow-sm"
                          >
                            <div
                              className={`h-11 w-11 shrink-0 rounded-xl bg-gradient-to-br ${getRoleGradient(
                                u.role_name
                              )} flex items-center justify-center font-bold text-base shadow-sm group-hover:scale-105 transition-transform`}
                            >
                              {u.name.charAt(0).toUpperCase()}
                            </div>

                            <div className="flex flex-col truncate">
                              <span className="font-bold text-sm text-foreground truncate group-hover:text-primary transition-colors">
                                {u.name}
                              </span>
                              <div className="flex items-center gap-1 mt-0.5">
                                <Badge
                                  variant="secondary"
                                  className="text-[10px] px-1.5 py-0 font-medium bg-background/80 text-muted-foreground border"
                                >
                                  {u.role_name || "Usuário"}
                                </Badge>
                              </div>
                            </div>
                          </button>
                        ))}
                      </div>

                      {quickUsers.length === 0 && !loadingQuickUsers && (
                        <div className="p-6 text-center text-xs text-muted-foreground border rounded-xl bg-muted/20">
                          Nenhum usuário em card disponível. Alterne para o login manual por e-mail abaixo.
                        </div>
                      )}
                    </div>
                  )}

                  {/* Mode Toggle Button */}
                  <div className="pt-2 border-t flex items-center justify-between">
                    <Button
                      type="button"
                      variant="ghost"
                      className="text-xs text-muted-foreground hover:text-foreground gap-1.5 px-2"
                      onClick={() => setLoginMode("manual")}
                    >
                      <Mail className="h-3.5 w-3.5 text-primary" /> Entrar com outro e-mail & senha
                    </Button>
                  </div>
                </div>
              )}

              {/* MANUAL LOGIN MODE */}
              {loginMode === "manual" && (
                <div className="space-y-4">
                  <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="email">E-mail de Acesso</Label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="email"
                          type="email"
                          placeholder="seu.email@empresa.com.br"
                          className="pl-9"
                          {...register("email")}
                        />
                      </div>
                      {errors.email && (
                        <p className="text-xs text-destructive mt-1">{errors.email.message}</p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="password">Senha de Acesso</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="password"
                          type={showPassword ? "text" : "password"}
                          placeholder="••••••••"
                          className="pl-9 pr-9"
                          {...register("password")}
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground transition-colors"
                          tabIndex={-1}
                        >
                          {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </button>
                      </div>
                      {errors.password && (
                        <p className="text-xs text-destructive mt-1">{errors.password.message}</p>
                      )}
                    </div>

                    <Button type="submit" className="w-full h-10 gap-2 font-semibold" disabled={isSubmitting}>
                      {isSubmitting ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" /> Autenticando...
                        </>
                      ) : (
                        <>
                          Entrar no Sistema <ArrowRight className="h-4 w-4" />
                        </>
                      )}
                    </Button>
                  </form>

                  <div className="pt-2 border-t flex items-center justify-between">
                    <Button
                      type="button"
                      variant="ghost"
                      className="text-xs text-muted-foreground hover:text-foreground gap-1.5 px-2"
                      onClick={() => {
                        setLoginMode("cards");
                        setSelectedUser(null);
                      }}
                    >
                      <KeyRound className="h-3.5 w-3.5 text-primary" /> Voltar para Acesso por Cards
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Footer info */}
        <div className="w-full max-w-lg mx-auto text-center text-xs text-muted-foreground">
          Conexão Segura com Criptografia Argon2id & JWT Local-First
        </div>
      </div>
    </div>
  );
}
