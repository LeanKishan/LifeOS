import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import Constants from "expo-constants";
import * as SecureStore from "expo-secure-store";

/**
 * Same contract and refresh semantics as the web client
 * (`frontend/src/lib/api.ts`); the differences are all platform:
 * tokens live in the device keychain (async) instead of localStorage, and
 * "auth cleared" is a listener set rather than a DOM event.
 */

const extra = (Constants.expoConfig?.extra ?? {}) as { apiUrl?: string };
export const baseURL =
  process.env.EXPO_PUBLIC_API_URL ?? extra.apiUrl ?? "http://localhost:8000/api";

export const api = axios.create({ baseURL });

const ACCESS_KEY = "lifeos.accessToken";
const REFRESH_KEY = "lifeos.refreshToken";

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

let accessTokenCache: string | null = null;

export async function loadTokens(): Promise<{ access: string | null; refresh: string | null }> {
  const [access, refresh] = await Promise.all([
    SecureStore.getItemAsync(ACCESS_KEY),
    SecureStore.getItemAsync(REFRESH_KEY),
  ]);
  accessTokenCache = access;
  return { access, refresh };
}

export async function setTokens(tokens: TokenPair | null): Promise<void> {
  if (!tokens) {
    accessTokenCache = null;
    await Promise.all([
      SecureStore.deleteItemAsync(ACCESS_KEY),
      SecureStore.deleteItemAsync(REFRESH_KEY),
    ]);
    return;
  }
  accessTokenCache = tokens.access_token;
  await Promise.all([
    SecureStore.setItemAsync(ACCESS_KEY, tokens.access_token),
    SecureStore.setItemAsync(REFRESH_KEY, tokens.refresh_token),
  ]);
}

// --- auth-cleared fan-out (the auth provider subscribes) ---
type Listener = () => void;
const authClearedListeners = new Set<Listener>();

export function onAuthCleared(listener: Listener): () => void {
  authClearedListeners.add(listener);
  return () => authClearedListeners.delete(listener);
}

function broadcastAuthCleared(): void {
  authClearedListeners.forEach((fn) => fn());
}

// --- interceptors ---
api.interceptors.request.use((config) => {
  if (accessTokenCache) {
    config.headers.Authorization = `Bearer ${accessTokenCache}`;
  }
  return config;
});

type RetriableConfig = InternalAxiosRequestConfig & { _retried?: boolean };

let pendingRefresh: Promise<string | null> | null = null;

async function runRefresh(): Promise<string | null> {
  const refresh_token = await SecureStore.getItemAsync(REFRESH_KEY);
  if (!refresh_token) return null;
  try {
    const { data } = await axios.post<TokenPair>(`${baseURL}/auth/refresh`, { refresh_token });
    await setTokens(data);
    return data.access_token;
  } catch {
    await setTokens(null);
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
