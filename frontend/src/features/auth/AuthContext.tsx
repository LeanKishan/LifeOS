import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { AUTH_CLEARED_EVENT, getAccessToken, setTokens } from "@/lib/api";
import { loginRequest, meRequest, registerRequest, type AuthUser } from "@/features/auth/api";

type AuthStatus = "loading" | "authenticated" | "anonymous";

interface AuthContextValue {
  user: AuthUser | null;
  status: AuthStatus;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");

  useEffect(() => {
    let cancelled = false;

    async function hydrate(): Promise<void> {
      if (!getAccessToken()) {
        if (!cancelled) setStatus("anonymous");
        return;
      }
      try {
        const me = await meRequest();
        if (!cancelled) {
          setUser(me);
          setStatus("authenticated");
        }
      } catch {
        setTokens(null);
        if (!cancelled) {
          setUser(null);
          setStatus("anonymous");
        }
      }
    }

    void hydrate();

    const onCleared = (): void => {
      setUser(null);
      setStatus("anonymous");
    };
    window.addEventListener(AUTH_CLEARED_EVENT, onCleared);
    return () => {
      cancelled = true;
      window.removeEventListener(AUTH_CLEARED_EVENT, onCleared);
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await loginRequest(email, password);
    setTokens(tokens);
    setUser(await meRequest());
    setStatus("authenticated");
  }, []);

  const register = useCallback(
    async (email: string, password: string, fullName: string) => {
      const full_name = fullName.trim();
      await registerRequest({ email, password, full_name: full_name || undefined });
      await login(email, password);
    },
    [login],
  );

  const logout = useCallback(() => {
    setTokens(null);
    setUser(null);
    setStatus("anonymous");
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, status, login, register, logout }),
    [user, status, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
