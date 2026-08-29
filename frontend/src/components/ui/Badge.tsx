import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

export type Tone =
  | "neutral"
  | "brand"
  | "blue"
  | "violet"
  | "amber"
  | "rose"
  | "emerald";

const TONE: Record<Tone, string> = {
  neutral: "bg-line/[0.06] text-muted ring-line/10",
  brand: "bg-brand/10 text-brand-hi ring-brand/20",
  emerald: "bg-emerald-500/12 text-emerald-300 ring-emerald-500/20",
  blue: "bg-blue-500/12 text-blue-300 ring-blue-500/20",
  violet: "bg-violet-500/12 text-violet-300 ring-violet-500/20",
  amber: "bg-amber-500/12 text-amber-300 ring-amber-500/20",
  rose: "bg-rose-500/12 text-rose-300 ring-rose-500/20",
};

export function Badge({
  tone = "neutral",
  dot,
  children,
  className,
}: {
  tone?: Tone;
  dot?: boolean;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span className={cn("pill", TONE[tone], className)}>
      {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" />}
      {children}
    </span>
  );
}
