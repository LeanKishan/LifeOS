import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

const baseURL = import.meta.env.VITE_API_URL ?? "/api";

export const api = axios.create({ baseURL });

const ACCESS_KEY = "lifeos.accessToken";
const REFRESH_KEY = "lifeos.refreshToken";

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}

export function setTokens(tokens: TokenPair | null): void {
  if (!tokens) {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    return;
  }
  localStorage.setItem(ACCESS_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
}

/** Fired when tokens are dropped so the auth context can react and guards redirect. */
export const AUTH_CLEARED_EVENT = "lifeos:auth-cleared";

function broadcastAuthCleared(): void {
  window.dispatchEvent(new Event(AUTH_CLEARED_EVENT));
}

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

type RetriableConfig = InternalAxiosRequestConfig & { _retried?: boolean };

// Coalesce concurrent 401s onto a single refresh call.
let pendingRefresh: Promise<string | null> | null = null;

async function runRefresh(): Promise<string | null> {
  const refresh_token = getRefreshToken();
  if (!refresh_token) return null;
  try {
    const { data } = await axios.post<TokenPair>(`${baseURL}/auth/refresh`, { refresh_token });
    setTokens(data);
    return data.access_token;
  } catch {
    setTokens(null);
    broadcastAuthCleared();
    return null;
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined;
    const isRefreshCall = original?.url?.includes("/auth/refresh") ?? false;

    if (error.response?.status === 401 && original && !original._retried && !isRefreshCall) {
      original._retried = true;
      pendingRefresh ??= runRefresh().finally(() => {
        pendingRefresh = null;
      });
      const newAccess = await pendingRefresh;
      if (newAccess) {
        original.headers.Authorization = `Bearer ${newAccess}`;
        return api(original);
      }
    }
    return Promise.reject(error);
  },
);
