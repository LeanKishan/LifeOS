import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { api, loadTokens, onAuthCleared, setTokens, type TokenPair } from "@/lib/api";

type Status = "loading" | "authenticated" | "anonymous";

interface AuthValue {
  status: Status;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<Status>("loading");

  useEffect(() => {
    loadTokens().then(({ access }) => setStatus(access ? "authenticated" : "anonymous"));
    return onAuthCleared(() => setStatus("anonymous"));
  }, []);

  const value = useMemo<AuthValue>(() => {
    async function authenticate(path: string, email: string, password: string) {
      if (path === "register") {
        await api.post("/auth/register", { email, password });
      }
      // OAuth2 password form, matching the web client.
      const body = new URLSearchParams({ username: email, password });
      const { data } = await api.post<TokenPair>("/auth/login", body.toString(), {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      await setTokens(data);
      setStatus("authenticated");
    }

    return {
      status,
      signIn: (email, password) => authenticate("login", email, password),
      signUp: (email, password) => authenticate("register", email, password),
      signOut: async () => {
        await setTokens(null);
        setStatus("anonymous");
      },
    };
  }, [status]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}
