import type { ReactNode } from "react";

import { Icon } from "@/components/icons";
import { Button } from "@/components/ui";

export function AuthShell({
  title,
  subtitle,
  error,
  children,
}: {
  title: string;
  subtitle?: string;
  error: string | null;
  children: ReactNode;
}) {
  return (
    <div className="relative grid min-h-screen lg:grid-cols-2">
      <div className="relative hidden overflow-hidden border-r border-line/[0.08] bg-elev/40 p-12 lg:flex lg:flex-col lg:justify-between">
        <div className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute -left-24 top-10 h-96 w-96 animate-aurora rounded-full bg-brand/15 blur-[110px]" />
          <div className="absolute bottom-0 right-0 h-96 w-96 animate-aurora rounded-full bg-violet-500/12 blur-[110px] [animation-delay:-9s]" />
        </div>
        <div className="flex items-center gap-2.5">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-brand-hi to-brand-lo text-[#04140d] shadow-glow-sm">
            <Icon name="layers" size={18} strokeWidth={2.2} />
          </span>
          <span className="font-display text-lg font-extrabold tracking-tight">
            Life<span className="text-brand-hi">OS</span>
          </span>
        </div>
        <div className="max-w-md">
          <h2 className="font-display text-4xl font-extrabold leading-tight tracking-tight">
            Everything you run,
            <br />
            <span className="text-gradient">in one place.</span>
          </h2>
          <p className="mt-4 text-muted">
            Job search, projects, calendar, finances, learning — one login, one
            timeline, and an assistant that acts on all of it.
          </p>
          <ul className="mt-6 space-y-2 text-sm text-muted">
            {[
              "Kanban + calendar with recurrence",
              "Budgets & analytics that add up",
              "Streaming AI assistant",
            ].map((f) => (
              <li key={f} className="flex items-center gap-2">
                <Icon name="check" size={15} className="text-brand-hi" />
                {f}
              </li>
            ))}
          </ul>
        </div>
        <p className="text-xs text-faint">Built milestone by milestone · open source</p>
      </div>

      <div className="relative flex items-center justify-center overflow-hidden p-6 sm:p-12">
        <div className="pointer-events-none absolute inset-0 -z-10 lg:hidden">
          <div className="absolute -left-24 -top-24 h-80 w-80 rounded-full bg-brand/12 blur-[100px]" />
        </div>
        <div className="w-full max-w-sm animate-fade-in-up">
          <div className="mb-8 flex items-center gap-2.5 lg:hidden">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-brand-hi to-brand-lo text-[#04140d]">
              <Icon name="layers" size={18} strokeWidth={2.2} />
            </span>
            <span className="font-display text-lg font-extrabold">
              Life<span className="text-brand-hi">OS</span>
            </span>
          </div>
          <h1 className="font-display text-2xl font-bold">{title}</h1>
          {subtitle && <p className="mt-1 text-sm text-muted">{subtitle}</p>}
          {error && (
            <p
              role="alert"
              className="mt-4 flex items-center gap-2 rounded-xl border border-rose-500/25 bg-rose-500/10 px-3 py-2.5 text-sm text-rose-300"
            >
              <Icon name="x" size={15} />
              {error}
            </p>
          )}
          <div className="mt-6">{children}</div>
        </div>
      </div>
    </div>
  );
}

export function Field({
  label,
  type,
  value,
  onChange,
  autoComplete,
  required = true,
}: {
  label: string;
  type: "text" | "email" | "password";
  value: string;
  onChange: (value: string) => void;
  autoComplete?: string;
  required?: boolean;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-[13px] font-medium text-muted">{label}</span>
      <input
        type={type}
        value={value}
        required={required}
        autoComplete={autoComplete}
        onChange={(event) => onChange(event.target.value)}
        className="field-input"
      />
    </label>
  );
}

export function SubmitButton({ busy, children }: { busy: boolean; children: ReactNode }) {
  return (
    <Button type="submit" variant="primary" size="lg" block loading={busy} iconRight="arrowRight">
      {children}
    </Button>
  );
}
