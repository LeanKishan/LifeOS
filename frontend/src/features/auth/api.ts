import { api, type TokenPair } from "@/lib/api";

export interface AuthUser {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export async function registerRequest(input: {
  email: string;
  password: string;
  full_name?: string;
}): Promise<AuthUser> {
  const { data } = await api.post<AuthUser>("/auth/register", input);
  return data;
}

export async function loginRequest(email: string, password: string): Promise<TokenPair> {
  const body = new URLSearchParams({ username: email, password });
  const { data } = await api.post<TokenPair>("/auth/login", body, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data;
}

export async function meRequest(): Promise<AuthUser> {
  const { data } = await api.get<AuthUser>("/auth/me");
  return data;
}

export async function logoutRequest(refreshToken: string): Promise<void> {
  await api.post("/auth/logout", { refresh_token: refreshToken });
}

export async function logoutAllRequest(): Promise<void> {
  await api.post("/auth/logout-all");
}
