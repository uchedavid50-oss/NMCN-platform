"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api, User } from "./api";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  loading: boolean;
 login: (email: string, password: string, totpCode?: string) => Promise<User>;
  refreshUser: () => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const TOKEN_KEY = "nmcn_access_token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (stored) {
      setToken(stored);
      api
        .me(stored)
        .then(setUser)
        .catch(() => {
          localStorage.removeItem(TOKEN_KEY);
          setToken(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

 async function login(email: string, password: string, totpCode?: string) {
    const { access_token } = await api.login(email, password, totpCode);
    localStorage.setItem(TOKEN_KEY, access_token);
    setToken(access_token);
    const me = await api.me(access_token);
    setUser(me);
    return me;
  }

  /** Re-fetches /auth/me -- used after payment so the route guard sees the
   * new subscription_status without a full page reload. */
  async function refreshUser() {
    if (token) setUser(await api.me(token));
  }

  async function signup(email: string, password: string) {
    // Deliberately does not auto-login -- new accounts start unverified and
    // login is blocked until the student clicks the emailed verification
    // link, so an immediate login attempt here would just fail.
    await api.signup(email, password);
  }

  async function logout() {
    if (token) {
      try {
        await api.logout(token);
      } catch {
        // Best-effort -- still clear local state even if the backend call
        // fails (e.g. session already gone), so the user isn't stuck.
      }
    }
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, signup, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
