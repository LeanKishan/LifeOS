import { useEffect, useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, NavLink, useLocation } from "react-router-dom";

import { Icon, type IconName } from "@/components/icons";
import { useAuth } from "@/features/auth/AuthContext";
import { useLiveUpdates } from "@/features/realtime/useLiveUpdates";
import { api } from "@/lib/api";
import { cn } from "@/lib/cn";

export const NAV: { to: string; label: string; icon: IconName }[] = [
  { to: "/", label: "Dashboard", icon: "dashboard" },
  { to: "/job-tracker", label: "Job Tracker", icon: "briefcase" },
  { to: "/projects", label: "Projects", icon: "kanban" },
  { to: "/calendar", label: "Calendar", icon: "calendar" },
  { to: "/finance", label: "Finance", icon: "wallet" },
  { to: "/learning", label: "Learning", icon: "book" },
  { to: "/analytics", label: "Analytics", icon: "chart" },
  { to: "/coach", label: "Assistant", icon: "sparkles" },
  { to: "/settings", label: "Settings", icon: "settings" },
];

function Brand() {
  return (
    <Link to="/" className="group flex items-center gap-2.5">
      <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-brand-hi to-brand-lo text-[#04140d] shadow-glow-sm transition group-hover:shadow-glow">
        <Icon name="layers" size={18} strokeWidth={2.2} />
      </span>
      <span className="font-display text-lg font-extrabold tracking-tight">
        Life<span className="text-brand-hi">OS</span>
      </span>
    </Link>
  );
}

function NavItems({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="flex flex-col gap-1">
      {NAV.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.to === "/"}
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition",
              isActive
                ? "bg-brand/10 text-brand-hi"
                : "text-muted hover:bg-line/[0.05] hover:text-content",
            )
          }
        >
          {({ isActive }) => (
            <>
              {isActive && (
                <span className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-brand-hi" />
              )}
              <Icon name={item.icon} size={18} />
              {item.label}
            </>
          )}
        </NavLink>
      ))}
    </nav>
  );
}

function HealthDot() {
  const { data, isError } = useQuery({
    queryKey: ["health"],
    queryFn: async () => (await api.get<{ status: string; database: string }>("/health")).data,
    refetchInterval: 30_000,
  });
  const ok = !isError && data?.status === "ok" && data?.database === "ok";
  return (
    <span
      title={ok ? "API + database healthy" : "API degraded"}
      className={cn(
        "hidden items-center gap-1.5 rounded-full border border-line/[0.1] bg-surface-2 px-2.5 py-1 text-[11px] font-medium sm:inline-flex",
        ok ? "text-brand-hi" : "text-amber-300",
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", ok ? "bg-brand-hi" : "bg-amber-400")} />
      {ok ? "systems ok" : "degraded"}
    </span>
  );
}

function UserMenu() {
  const { user, logout, logoutEverywhere } = useAuth();
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (!open) return;
    const close = () => setOpen(false);
    window.addEventListener("click", close);
    return () => window.removeEventListener("click", close);
  }, [open]);

  return (
    <div className="relative" onClick={(e) => e.stopPropagation()}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-xl border border-line/[0.1] bg-surface-2 py-1 pl-1 pr-2.5 text-sm transition hover:border-brand/40"
      >
        <span className="grid h-7 w-7 place-items-center rounded-lg bg-gradient-to-br from-brand-hi to-brand-lo text-[11px] font-bold text-[#04140d]">
          {(user?.email ?? "?").slice(0, 2).toUpperCase()}
        </span>
        <span className="hidden max-w-[10rem] truncate text-muted sm:inline">{user?.email}</span>
        <Icon name="chevronDown" size={14} className="text-faint" />
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-2 w-56 origin-top-right animate-scale-in rounded-xl border border-line/[0.1] bg-elev p-1.5 shadow-pop">
          <div className="truncate px-2.5 py-2 text-xs text-faint">{user?.email}</div>
          <Link
            to="/settings"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm text-muted hover:bg-line/[0.05] hover:text-content"
          >
            <Icon name="settings" size={15} /> Settings
          </Link>
          <button
            type="button"
            onClick={() => void logout()}
            className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm text-muted hover:bg-line/[0.05] hover:text-content"
          >
            <Icon name="logout" size={15} /> Log out
          </button>
          <button
            type="button"
            onClick={() => void logoutEverywhere()}
            className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-xs text-faint hover:bg-rose-500/10 hover:text-rose-300"
          >
            Log out everywhere
          </button>
        </div>
      )}
    </div>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const { status } = useAuth();
  const { connected } = useLiveUpdates(status === "authenticated");
  const { pathname } = useLocation();
  const [drawer, setDrawer] = useState(false);

  useEffect(() => setDrawer(false), [pathname]);

  return (
    <div className="min-h-screen">
      {/* ambient background */}
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -left-40 -top-40 h-[32rem] w-[32rem] animate-aurora rounded-full bg-brand/12 blur-[120px]" />
        <div className="absolute -right-40 top-1/3 h-[28rem] w-[28rem] animate-aurora rounded-full bg-violet-500/10 blur-[120px] [animation-delay:-8s]" />
      </div>

      {/* desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-line/[0.08] bg-elev/60 px-4 py-5 backdrop-blur-xl lg:flex">
        <div className="px-2">
          <Brand />
        </div>
        <div className="mt-8 flex-1 overflow-y-auto">
          <NavItems />
        </div>
        <div className="mt-4 border-t border-line/[0.08] pt-3">
          <span
            className={cn(
              "flex items-center gap-2 px-3 text-[11px] font-medium",
              connected ? "text-brand-hi" : "text-faint",
            )}
          >
            <Icon name="live" size={13} className={connected ? "" : "opacity-40"} />
            {connected ? "Live updates on" : "Reconnecting…"}
          </span>
        </div>
      </aside>

      {/* mobile drawer */}
      {drawer && (
        <div className="fixed inset-0 z-40 lg:hidden" onClick={() => setDrawer(false)}>
          <div className="absolute inset-0 bg-ink/70 backdrop-blur-sm" />
          <div
            className="absolute inset-y-0 left-0 w-72 animate-slide-in-right border-r border-line/[0.1] bg-elev px-4 py-5"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-2">
              <Brand />
              <button type="button" onClick={() => setDrawer(false)} className="btn-ghost btn-sm">
                <Icon name="x" size={18} />
              </button>
            </div>
            <div className="mt-6">
              <NavItems onNavigate={() => setDrawer(false)} />
            </div>
          </div>
        </div>
      )}

      <div className="lg:pl-64">
        {/* topbar */}
        <header className="sticky top-0 z-20 border-b border-line/[0.08] bg-ink/70 backdrop-blur-xl">
          <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-3 px-4 sm:px-8">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setDrawer(true)}
                className="btn-ghost btn-sm lg:hidden"
                aria-label="Menu"
              >
                <Icon name="menu" size={20} />
              </button>
              <span className="lg:hidden">
                <Brand />
              </span>
            </div>
            <div className="flex items-center gap-2.5">
              <HealthDot />
              <UserMenu />
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-6xl px-4 py-8 sm:px-8">
          <div key={pathname} className="animate-fade-in-up">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
