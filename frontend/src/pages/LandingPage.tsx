import { useState } from "react";
import { Link } from "react-router-dom";

import { Icon, type IconName } from "@/components/icons";
import { Button } from "@/components/ui";
import { cn } from "@/lib/cn";

const FEATURES: { icon: IconName; title: string; body: string }[] = [
  {
    icon: "briefcase",
    title: "Job Tracker",
    body: "A pipeline from wishlist to offer — companies, interviews, contacts, and a live response-rate stat.",
  },
  {
    icon: "kanban",
    title: "Projects",
    body: "Drag-and-drop Kanban boards with custom columns, priorities, labels, subtasks and comments.",
  },
  {
    icon: "calendar",
    title: "Calendar",
    body: "Month and week views with iCalendar recurrence — and per-occurrence edits when one meeting moves.",
  },
  {
    icon: "wallet",
    title: "Finance",
    body: "Accounts, categorised transactions in integer cents, monthly budgets, CSV import and a PDF report.",
  },
  {
    icon: "book",
    title: "Learning",
    body: "Courses and lessons with progress, plus SM-2 spaced-repetition flashcards and a daily review queue.",
  },
  {
    icon: "sparkles",
    title: "AI Assistant",
    body: "A streaming, tool-using chat that reads your data and can add tasks, events and flashcards for you.",
  },
];

const STACK = [
  "React 19",
  "TypeScript",
  "FastAPI",
  "PostgreSQL",
  "Redis",
  "Celery",
  "Docker",
  "Terraform",
  "GitHub Actions",
];

function Nav() {
  const [open, setOpen] = useState(false);
  return (
    <header className="sticky top-0 z-30 border-b border-line/[0.06] bg-ink/70 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-2.5">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-brand-hi to-brand-lo text-[#04140d] shadow-glow-sm">
            <Icon name="layers" size={18} strokeWidth={2.2} />
          </span>
          <span className="font-display text-lg font-extrabold tracking-tight">
            Life<span className="text-brand-hi">OS</span>
          </span>
        </Link>

        <nav className="hidden items-center gap-8 text-sm text-muted md:flex">
          <a href="#features" className="transition hover:text-content">Features</a>
          <a href="#stack" className="transition hover:text-content">Stack</a>
          <a
            href="https://github.com/LeanKishan/LifeOS"
            target="_blank"
            rel="noreferrer"
            className="transition hover:text-content"
          >
            GitHub
          </a>
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          <Button to="/login" variant="ghost">Log in</Button>
          <Button to="/register" variant="primary" iconRight="arrowRight">Get started</Button>
        </div>

        <button
          type="button"
          className="btn-ghost btn-sm md:hidden"
          onClick={() => setOpen((o) => !o)}
          aria-label="Menu"
        >
          <Icon name={open ? "x" : "menu"} size={20} />
        </button>
      </div>
      {open && (
        <div className="border-t border-line/[0.06] px-4 py-4 md:hidden">
          <div className="flex flex-col gap-2">
            <Button to="/login" variant="secondary" block>Log in</Button>
            <Button to="/register" variant="primary" block iconRight="arrowRight">
              Get started
            </Button>
          </div>
        </div>
      )}
    </header>
  );
}

function WindowMock() {
  return (
    <div className="surface-glass mx-auto w-full max-w-3xl overflow-hidden rounded-2xl p-0 shadow-pop">
      <div className="flex items-center gap-2 border-b border-line/[0.06] px-4 py-3">
        <span className="h-3 w-3 rounded-full bg-rose-400/70" />
        <span className="h-3 w-3 rounded-full bg-amber-400/70" />
        <span className="h-3 w-3 rounded-full bg-brand-hi/70" />
        <span className="ml-3 hidden rounded-md bg-line/[0.06] px-3 py-1 text-[11px] text-faint sm:block">
          lifeos.app / dashboard
        </span>
      </div>
      <div className="flex">
        <div className="hidden w-14 shrink-0 flex-col items-center gap-3 border-r border-line/[0.06] py-4 sm:flex">
          {(["dashboard", "briefcase", "kanban", "calendar", "wallet", "chart"] as IconName[]).map(
            (n, i) => (
              <span
                key={n}
                className={cn(
                  "grid h-8 w-8 place-items-center rounded-lg",
                  i === 0 ? "bg-brand/15 text-brand-hi" : "text-faint",
                )}
              >
                <Icon name={n} size={16} />
              </span>
            ),
          )}
        </div>
        <div className="flex-1 p-4 sm:p-5">
          <div className="text-sm font-semibold">
            Good evening, <span className="text-gradient">Alex</span>
          </div>
          <div className="mt-1 text-xs text-faint">Here's everything at a glance.</div>
          <div className="mt-4 grid grid-cols-2 gap-2.5 sm:grid-cols-4">
            {[
              ["Applications", "14"],
              ["Active", "12"],
              ["Response", "67%"],
              ["Offers", "2"],
            ].map(([l, v]) => (
              <div key={l} className="rounded-xl border border-line/[0.07] bg-ink/40 p-2.5">
                <div className="text-[9px] font-semibold uppercase tracking-wider text-faint">
                  {l}
                </div>
                <div className="mt-1 text-base font-bold tabular-nums">{v}</div>
              </div>
            ))}
          </div>
          <div className="mt-3 flex items-end gap-1.5 rounded-xl border border-line/[0.07] bg-ink/40 p-3">
            {[40, 62, 48, 80, 56, 92, 70, 100, 64].map((h, i) => (
              <span
                key={i}
                className="flex-1 rounded-sm bg-gradient-to-t from-brand/40 to-brand-hi"
                style={{ height: `${h * 0.5}px` }}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LandingPage() {
  return (
    <div className="min-h-dvh">
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -left-40 -top-40 h-[34rem] w-[34rem] animate-aurora rounded-full bg-brand/[0.12] blur-[130px]" />
        <div className="absolute right-0 top-1/4 h-[30rem] w-[30rem] animate-aurora rounded-full bg-violet-500/[0.1] blur-[130px] [animation-delay:-9s]" />
      </div>

      <Nav />

      {/* hero */}
      <section className="mx-auto max-w-6xl px-4 pb-16 pt-16 text-center sm:px-6 sm:pt-24 lg:px-8">
        <span className="inline-flex items-center gap-2 rounded-full border border-line/[0.1] bg-surface-2 px-3 py-1 text-xs font-medium text-muted animate-fade-in-up">
          <span className="h-1.5 w-1.5 rounded-full bg-brand-hi" />
          One workspace for the whole of it
        </span>
        <h1 className="mx-auto mt-6 max-w-3xl font-display text-4xl font-extrabold leading-[1.05] tracking-tight animate-fade-in-up stagger-1 sm:text-6xl">
          Everything you run,
          <br />
          <span className="text-gradient">in one place.</span>
        </h1>
        <p className="mx-auto mt-5 max-w-xl text-base text-muted animate-fade-in-up stagger-2 sm:text-lg">
          Job search, projects, calendar, finances and learning — one login, one
          timeline, and an assistant that acts across all of it.
        </p>
        <div className="mt-8 flex flex-col items-center justify-center gap-3 animate-fade-in-up stagger-3 sm:flex-row">
          <Button to="/register" variant="primary" size="lg" iconRight="arrowRight">
            Get started — it's free
          </Button>
          <Button to="/login" variant="secondary" size="lg">
            Log in
          </Button>
        </div>
        <div className="mt-14 animate-fade-in-up stagger-4">
          <WindowMock />
        </div>
      </section>

      {/* features */}
      <section id="features" className="mx-auto max-w-6xl scroll-mt-20 px-4 py-16 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">
            Six tools, one system
          </h2>
          <p className="mt-3 text-muted">
            Every module shares the same login, database and design — and the
            assistant can reach all of them.
          </p>
        </div>
        <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f, i) => (
            <div
              key={f.title}
              className={cn(
                "surface-card card-hover p-6 animate-fade-in-up",
                `stagger-${Math.min(i + 1, 6)}`,
              )}
            >
              <span className="grid h-11 w-11 place-items-center rounded-xl bg-brand/10 text-brand-hi">
                <Icon name={f.icon} size={20} />
              </span>
              <h3 className="mt-4 font-semibold text-content">{f.title}</h3>
              <p className="mt-1.5 text-sm text-muted">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* integration band */}
      <section className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="surface-glass overflow-hidden rounded-3xl p-8 text-center sm:p-12">
          <h2 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">
            The point is that it's <span className="text-gradient">connected</span>.
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-muted">
            An interview lands on the calendar. A budget overrun shows in analytics.
            "Add prep to my board for Friday" just works — because it's all one API.
          </p>
        </div>
      </section>

      {/* stack */}
      <section id="stack" className="mx-auto max-w-6xl scroll-mt-20 px-4 py-16 text-center sm:px-6 lg:px-8">
        <h2 className="label-eyebrow">Built with</h2>
        <div className="mt-5 flex flex-wrap items-center justify-center gap-2.5">
          {STACK.map((s) => (
            <span
              key={s}
              className="rounded-full border border-line/[0.1] bg-surface-2 px-3.5 py-1.5 text-sm text-muted"
            >
              {s}
            </span>
          ))}
        </div>
        <p className="mx-auto mt-6 max-w-lg text-sm text-faint">
          A real full-stack build — sync SQLAlchemy, Alembic migrations, JWT auth
          with token revocation, Celery jobs, WebSocket live updates, Prometheus
          metrics, and an ECS Fargate Terraform stack.
        </p>
      </section>

      {/* final CTA */}
      <section className="mx-auto max-w-6xl px-4 pb-24 sm:px-6 lg:px-8">
        <div className="relative overflow-hidden rounded-3xl border border-brand/20 bg-gradient-to-b from-brand/[0.08] to-transparent p-10 text-center sm:p-16">
          <h2 className="font-display text-3xl font-extrabold tracking-tight sm:text-4xl">
            Start running your life like a product.
          </h2>
          <div className="mt-8 flex justify-center">
            <Button to="/register" variant="primary" size="lg" iconRight="arrowRight">
              Create your workspace
            </Button>
          </div>
        </div>
      </section>

      <footer className="border-t border-line/[0.06]">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 py-8 text-sm text-faint sm:flex-row sm:px-6 lg:px-8">
          <div className="flex items-center gap-2">
            <span className="grid h-7 w-7 place-items-center rounded-lg bg-gradient-to-br from-brand-hi to-brand-lo text-[#04140d]">
              <Icon name="layers" size={14} strokeWidth={2.2} />
            </span>
            <span className="font-display font-bold text-muted">
              Life<span className="text-brand-hi">OS</span>
            </span>
          </div>
          <div className="flex items-center gap-5">
            <a
              href="https://github.com/LeanKishan/LifeOS"
              target="_blank"
              rel="noreferrer"
              className="transition hover:text-content"
            >
              Source
            </a>
            <span>© {new Date().getFullYear()}</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
