import { api } from "@/lib/api";

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
