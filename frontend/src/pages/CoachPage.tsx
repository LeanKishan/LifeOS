import { useEffect, useRef, useState, type FormEvent } from "react";

import { Icon } from "@/components/icons";
import { Button, PageHeader } from "@/components/ui";
import { sendChatStream, type ChatTurn } from "@/features/coach/api";
import { cn } from "@/lib/cn";

type Bubble = ChatTurn & { tools?: string[]; streaming?: boolean };

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

    const userTurn: ChatTurn = { role: "user", content: text };
    const history: ChatTurn[] = [
      ...bubbles.map(({ role, content }) => ({ role, content })),
      userTurn,
    ];
    setBubbles((prev) => [
      ...prev,
      userTurn,
      { role: "assistant", content: "", tools: [], streaming: true },
    ]);
    setInput("");
    setBusy(true);

    const patchLast = (fn: (b: Bubble) => Bubble) =>
      setBubbles((prev) => prev.map((b, i) => (i === prev.length - 1 ? fn(b) : b)));

    try {
      await sendChatStream(history, {
        onDelta: (chunk) => patchLast((b) => ({ ...b, content: b.content + chunk })),
        onTool: (name) => patchLast((b) => ({ ...b, tools: [...(b.tools ?? []), name] })),
        onDone: () => patchLast((b) => ({ ...b, streaming: false })),
        onError: () =>
          patchLast((b) => ({
            ...b,
            streaming: false,
            content: b.content || "Something went wrong — try again.",
          })),
        onUnavailable: () => {
          setUnavailable(true);
          setBubbles((prev) => prev.slice(0, -1));
        },
      });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title="Assistant" subtitle="It reads your data and can act on it." />

      {unavailable && (
        <p className="mb-4 flex items-center gap-2 rounded-xl border border-amber-500/25 bg-amber-500/10 px-3 py-2.5 text-sm text-amber-300">
          <Icon name="bell" size={15} />
          The assistant isn't configured on this server (no API key).
        </p>
      )}

      <div
        ref={scrollRef}
        className="surface-card mb-3 h-[28rem] space-y-4 overflow-y-auto p-5"
      >
        {bubbles.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
            <span className="grid h-12 w-12 place-items-center rounded-2xl bg-brand/10 text-brand-hi">
              <Icon name="sparkles" size={22} />
            </span>
            <p className="max-w-sm text-sm text-muted">
              Ask about your tasks, calendar, finances or flashcards — or tell it to add
              something.
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setInput(s)}
                  className="rounded-full border border-line/[0.12] bg-surface-2 px-3 py-1.5 text-xs text-muted transition hover:border-brand/40 hover:text-content"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {bubbles.map((bubble, index) => (
          <div
            key={index}
            className={cn("flex", bubble.role === "user" ? "justify-end" : "justify-start")}
          >
            <div
              className={cn(
                "max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm",
                bubble.role === "user"
                  ? "bg-gradient-to-b from-brand-hi to-brand text-[#04140d]"
                  : "border border-line/[0.08] bg-surface-2 text-content",
              )}
            >
              <p className="whitespace-pre-wrap">
                {bubble.content}
                {bubble.streaming && (
                  <span className="ml-0.5 inline-block h-3.5 w-1.5 animate-pulse rounded-sm bg-current align-middle" />
                )}
              </p>
              {bubble.tools && bubble.tools.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {bubble.tools.map((tool, i) => (
                    <span
                      key={`${tool}-${i}`}
                      className="inline-flex items-center gap-1 rounded-md bg-black/10 px-1.5 py-0.5 text-[10px] font-medium"
                    >
                      <Icon name="refresh" size={10} /> {tool}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={submit} className="flex gap-2">
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Message the assistant…"
          disabled={unavailable}
          className="field-input flex-1"
        />
        <Button
          type="submit"
          variant="primary"
          icon="send"
          loading={busy}
          disabled={unavailable}
        >
          Send
        </Button>
      </form>
    </div>
  );
}
