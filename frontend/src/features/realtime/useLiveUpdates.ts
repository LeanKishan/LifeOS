import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { getAccessToken } from "@/lib/api";

const WS_PATH = "/api/ws";
const MAX_BACKOFF_MS = 30_000;

function socketUrl(token: string): string {
  const envUrl = import.meta.env.VITE_API_URL;
  const query = `?token=${encodeURIComponent(token)}`;

  if (envUrl) {
    const url = new URL(envUrl);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    url.pathname = `${url.pathname.replace(/\/api\/?$/, "")}${WS_PATH}`;
    return `${url.origin}${url.pathname}${query}`;
  }

  const scheme = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${scheme}//${window.location.host}${WS_PATH}${query}`;
}

/**
 * Opens a WebSocket while `enabled`, and invalidates the query key named by each
 * incoming `{ type }` frame so other tabs refetch. Reconnects with backoff.
 */
export function useLiveUpdates(enabled: boolean): { connected: boolean } {
  const queryClient = useQueryClient();
  const token = getAccessToken();
  const [connected, setConnected] = useState(false);
  const attemptRef = useRef(0);

  useEffect(() => {
    if (!enabled || !token) return;

    let socket: WebSocket | null = null;
    let stopped = false;
    let timer: number | undefined;

    const open = (): void => {
      socket = new WebSocket(socketUrl(token));

      socket.onopen = () => {
        attemptRef.current = 0;
        setConnected(true);
      };

      socket.onmessage = (event) => {
        try {
          const frame = JSON.parse(String(event.data)) as { type?: string };
          if (frame.type && frame.type !== "connected") {
            void queryClient.invalidateQueries({ queryKey: [frame.type] });
          }
        } catch {
          /* ignore malformed frames */
        }
      };

      socket.onclose = () => {
        setConnected(false);
        if (stopped) return;
        const delay = Math.min(MAX_BACKOFF_MS, 1000 * 2 ** attemptRef.current++);
        timer = window.setTimeout(open, delay);
      };
    };

    open();

    return () => {
      stopped = true;
      if (timer) window.clearTimeout(timer);
      socket?.close();
    };
  }, [enabled, token, queryClient]);

  return { connected };
}
