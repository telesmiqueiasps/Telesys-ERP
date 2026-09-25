import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Layers,
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
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiFetch } from "@/lib/apiClient";
import { useAuthStore, UserMe } from "@/store/useAuthStore";
import { useAppStore } from "@/store/useAppStore";

const LoginSchema = z.object({
  email: z.string().min(1, "Informe o e-mail").email("Informe um e-mail válido"),
  password: z.string().min(1, "Informe a senha"),
});

type LoginFormValues = z.infer<typeof LoginSchema>;

export function LoginView() {
  const { setSession } = useAuthStore();
  const { theme, toggleTheme } = useAppStore();
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

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

  const fillDemoCredentials = () => {
    setValue("email", "admin@telesys.com.br", { shouldValidate: true });
    setValue("password", "admin123", { shouldValidate: true });
    setErrorMessage(null);
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
            <div className="h-11 w-11 rounded-xl bg-primary/20 backdrop-blur border border-primary/30 text-primary flex items-center justify-center font-bold shadow-lg shadow-primary/20">
              <Layers className="h-6 w-6 text-blue-400" />
            </div>
            <div>
              <span className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-white via-blue-100 to-blue-300 bg-clip-text text-transparent">
                Telesys ERP
              </span>
              <span className="text-xs ml-2 px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 font-medium border border-blue-500/30">
                + PDV
              </span>
            </div>
          </div>

          <Badge variant="outline" className="border-slate-700 bg-slate-800/60 text-slate-300">
            v0.1.0 Cloud Foundation
          </Badge>
        </div>

        {/* Feature Highlights */}
        <div className="relative z-10 space-y-8 my-auto">
          <div>
            <Badge variant="secondary" className="mb-4 bg-blue-500/10 text-blue-300 border-blue-500/20 gap-1.5 px-3 py-1">
              <Sparkles className="h-3.5 w-3.5 text-blue-400" /> Sistema Comercial Local-First
            </Badge>
            <h2 className="text-3xl font-extrabold tracking-tight leading-tight">
              Gestão ágil para MEIs, microempresas e pequenos comércios.
            </h2>
            <p className="mt-3 text-slate-400 text-sm leading-relaxed max-w-md">
              Operação diária com velocidade ultra-rápida no PDV local, sincronizada em nuvem com alta disponibilidade e segurança multiempresa.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4 pt-2">
            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/50 backdrop-blur space-y-2">
              <div className="h-8 w-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
                <Zap className="h-4 w-4" />
              </div>
              <h3 className="text-sm font-semibold text-slate-200">PDV Offline-First</h3>
              <p className="text-xs text-slate-400">Venda sem depender da internet no caixa com banco SQLite local.</p>
            </div>

            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/50 backdrop-blur space-y-2">
              <div className="h-8 w-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center">
                <ShieldCheck className="h-4 w-4" />
              </div>
              <h3 className="text-sm font-semibold text-slate-200">Segurança RBAC</h3>
              <p className="text-xs text-slate-400">Argon2id, JWT curto, permissões por função e segregação por tenant.</p>
            </div>
          </div>
        </div>

        {/* Footer info */}
        <div className="relative z-10 flex items-center justify-between text-xs text-slate-500 border-t border-slate-800/80 pt-6">
          <span>&copy; 2026 Telesys ERP. Todos os direitos reservados.</span>
          <div className="flex items-center gap-2 text-emerald-400 font-medium">
            <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            PostgreSQL Cloud Online
          </div>
        </div>
      </div>

      {/* Right Login Form Container */}
      <div className="w-full lg:w-1/2 flex flex-col justify-between p-6 sm:p-12">
        {/* Header Bar */}
        <div className="flex justify-between items-center w-full max-w-md mx-auto">
          <div className="lg:hidden flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center font-bold">
              <Layers className="h-4 w-4" />
            </div>
            <span className="font-bold tracking-tight text-base">Telesys ERP</span>
          </div>

          <div className="ml-auto flex items-center gap-2">
            <Button variant="ghost" size="icon" onClick={toggleTheme} title="Alternar tema">
              {theme === "light" ? <Moon className="h-4 w-4 text-slate-700" /> : <Sun className="h-4 w-4 text-amber-400" />}
            </Button>
          </div>
        </div>

        {/* Center Card */}
        <div className="w-full max-w-md mx-auto my-auto py-8">
          <Card className="border-border/60 shadow-xl shadow-black/5 backdrop-blur">
            <CardHeader className="space-y-1">
              <div className="flex items-center justify-between">
                <CardTitle className="text-2xl font-bold tracking-tight">Acessar Conta</CardTitle>
                <Badge variant="outline" className="text-xs font-normal">
                  Nuvem Cloud
                </Badge>
              </div>
              <CardDescription>
                Informe suas credenciais para entrar na plataforma Telesys
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              {errorMessage && (
                <div className="p-3.5 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-xs flex items-start gap-2.5 leading-relaxed animate-in fade-in-50">
                  <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                  <span>{errorMessage}</span>
                </div>
              )}

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
                  <div className="flex items-center justify-between">
                    <Label htmlFor="password">Senha de Acesso</Label>
                  </div>
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

              {/* Demo Quick Fill Button */}
              <div className="pt-3 border-t">
                <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
                  <span>Modo de Teste / Demonstração</span>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  className="w-full text-xs h-9 justify-start gap-2 text-slate-600 dark:text-slate-300"
                  onClick={fillDemoCredentials}
                >
                  <Sparkles className="h-3.5 w-3.5 text-amber-500" />
                  Preencher com Super Admin (admin@telesys.com.br)
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Footer info */}
        <div className="w-full max-w-md mx-auto text-center text-xs text-muted-foreground">
          Conexão Segura com Criptografia de Ponta a Ponta
        </div>
      </div>
    </div>
  );
}
