import { api, getAccessToken } from "@/lib/api";

export interface ChatTurn {
  role: "user" | "assistant";
  content: string;
}

export interface ChatReply {
  reply: string;
  tool_calls: string[];
}

export async function sendChat(messages: ChatTurn[]): Promise<ChatReply> {
  const { data } = await api.post<ChatReply>("/coach/chat", { messages });
  return data;
}

export interface StreamHandlers {
  onDelta: (text: string) => void;
  onTool: (name: string) => void;
  onDone: (toolCalls: string[]) => void;
  onError: () => void;
  onUnavailable: () => void;
}

/**
 * POST /coach/chat/stream and dispatch the server-sent events. Uses `fetch`
 * (axios doesn't expose the response body stream in the browser). A 401 falls
 * back to the non-streaming call, which runs through the axios refresh flow.
 */
export async function sendChatStream(
  messages: ChatTurn[],
  handlers: StreamHandlers,
): Promise<void> {
  const token = getAccessToken();
  const res = await fetch(`${api.defaults.baseURL ?? "/api"}/coach/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ messages }),
  });

  if (res.status === 503) return handlers.onUnavailable();
  if (res.status === 401) {
    const reply = await sendChat(messages);
    reply.tool_calls.forEach(handlers.onTool);
    if (reply.reply) handlers.onDelta(reply.reply);
    return handlers.onDone(reply.tool_calls);
  }
  if (!res.ok || !res.body) return handlers.onError();

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";
    for (const chunk of chunks) {
      const line = chunk.trim();
      if (!line.startsWith("data:")) continue;
      let event: { type: string; text?: string; name?: string; tool_calls?: string[] };
      try {
        event = JSON.parse(line.slice(5).trim());
      } catch {
        continue;
      }
      if (event.type === "delta" && event.text) handlers.onDelta(event.text);
      else if (event.type === "tool" && event.name) handlers.onTool(event.name);
      else if (event.type === "done") handlers.onDone(event.tool_calls ?? []);
      else if (event.type === "error") handlers.onError();
    }
  }
}
