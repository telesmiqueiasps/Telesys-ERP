import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface TenantInfo {
  id: string;
  name: string;
  document?: string | null;
  is_active: boolean;
}

export interface CompanyInfo {
  id: string;
  tenant_id: string;
  name: string;
  trade_name?: string | null;
  cnpj?: string | null;
  state_registration?: string | null;
  is_active: boolean;
}

export interface UserMe {
  id: string;
  tenant_id: string;
  name: string;
  email: string;
  is_superuser: boolean;
  tenant: TenantInfo;
  companies: CompanyInfo[];
  permissions: string[];
}

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: UserMe | null;
  activeCompany: CompanyInfo | null;
  isAuthenticated: boolean;
  setSession: (token: string, refreshToken: string, user: UserMe) => void;
  setActiveCompany: (company: CompanyInfo) => void;
  updateUser: (user: UserMe) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      refreshToken: null,
      user: null,
      activeCompany: null,
      isAuthenticated: false,

      setSession: (token: string, refreshToken: string, user: UserMe) => {
        const firstActiveCompany = user.companies && user.companies.length > 0 ? user.companies[0] : null;
        set({
          token,
          refreshToken,
          user,
          activeCompany: firstActiveCompany,
          isAuthenticated: true,
        });
      },

      setActiveCompany: (company: CompanyInfo) => set({ activeCompany: company }),

      updateUser: (user: UserMe) => set({ user }),

      logout: () =>
        set({
          token: null,
          refreshToken: null,
          user: null,
          activeCompany: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: "telesys-auth-session",
    }
  )
);
