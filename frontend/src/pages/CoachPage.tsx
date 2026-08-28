import { useEffect, useRef, useState, type FormEvent } from "react";

import { sendChat, type ChatTurn } from "@/features/coach/api";

type Bubble = ChatTurn & { tools?: string[] };

const SUGGESTIONS = [
  "What's on my agenda this week?",
  "Am I over budget this month?",
  "Add a task 'draft the README' to the LifeOS project",
];

export default function CoachPage() {
  const [bubbles, setBubbles] = useState<Bubble[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [bubbles, busy]);

  async function submit(event: FormEvent): Promise<void> {
    event.preventDefault();
    const text = input.trim();
    if (!text || busy) return;

    const withUser: Bubble[] = [...bubbles, { role: "user", content: text }];
    setBubbles(withUser);
    setInput("");
    setBusy(true);

    try {
      const history: ChatTurn[] = withUser.map(({ role, content }) => ({ role, content }));
      const reply = await sendChat(history);
      setBubbles([
        ...withUser,
        { role: "assistant", content: reply.reply, tools: reply.tool_calls },
      ]);
    } catch (err) {
      const status = (err as { response?: { status?: number } }).response?.status;
      if (status === 503) {
        setUnavailable(true);
      } else {
        setBubbles([
          ...withUser,
          { role: "assistant", content: "Something went wrong — try again.", tools: [] },
        ]);
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <h2 className="mb-4 text-xl font-semibold">Assistant</h2>

      {unavailable && (
        <p className="mb-4 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:bg-amber-950/50 dark:text-amber-300">
          The assistant isn't configured on this server (no API key).
        </p>
      )}

      <div
        ref={scrollRef}
        className="mb-3 h-[26rem] space-y-3 overflow-y-auto rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"
      >
        {bubbles.length === 0 && (
          <div className="space-y-2 text-sm text-slate-500">
            <p>Ask about your tasks, calendar, finances or flashcards — or tell me to add something.</p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => setInput(suggestion)}
                  className="rounded-full border border-slate-300 px-2.5 py-1 text-xs hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {bubbles.map((bubble, index) => (
          <div
            key={index}
            className={bubble.role === "user" ? "flex justify-end" : "flex justify-start"}
          >
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                bubble.role === "user"
                  ? "bg-emerald-600 text-white"
                  : "bg-slate-100 dark:bg-slate-800"
              }`}
            >
              <p className="whitespace-pre-wrap">{bubble.content}</p>
              {bubble.tools && bubble.tools.length > 0 && (
                <div className="mt-1.5 flex flex-wrap gap-1">
                  {bubble.tools.map((tool, toolIndex) => (
                    <span
                      key={`${tool}-${toolIndex}`}
                      className="rounded bg-slate-200 px-1.5 py-0.5 text-[10px] font-medium text-slate-600 dark:bg-slate-700 dark:text-slate-300"
                    >
                      {tool}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {busy && <p className="text-sm text-slate-400">thinking…</p>}
      </div>

      <form onSubmit={submit} className="flex gap-2">
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Message the assistant…"
          disabled={unavailable}
          className="flex-1 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-emerald-500 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-900"
        />
        <button
          type="submit"
          disabled={busy || unavailable}
          className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
