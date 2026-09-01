import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { api, clearSession, REFRESH_KEY, TOKEN_KEY } from "./api";
import type { AuthResponse, Role, UserProfile } from "./types";

interface AuthState {
  user: UserProfile | null;
  ready: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  hasRole: (r: Role) => boolean;
  setSession: (auth: AuthResponse) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [ready, setReady] = useState(false);

  async function loadUser() {
    if (!localStorage.getItem(TOKEN_KEY)) {
      setUser(null);
      return;
    }
    try {
      const { data } = await api.get<UserProfile>("/api/users/me");
      setUser(data);
    } catch {
      clearSession();
      setUser(null);
    }
  }

  useEffect(() => {
    loadUser().finally(() => setReady(true));
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      user,
      ready,
      isAuthenticated: !!user,
      isAdmin: user?.role === "ADMIN",
      hasRole: (r) => user?.role === r,
      setSession: async (auth) => {
        localStorage.setItem(TOKEN_KEY, auth.token);
        localStorage.setItem(REFRESH_KEY, auth.refreshToken);
        await loadUser();
      },
      logout: async () => {
        const refreshToken = localStorage.getItem(REFRESH_KEY);
        try {
          if (refreshToken) await api.post("/api/auth/logout", { refreshToken });
        } catch {
          /* ignore */
        }
        clearSession();
        setUser(null);
      },
      refreshUser: loadUser,
    }),
    [user, ready],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}
