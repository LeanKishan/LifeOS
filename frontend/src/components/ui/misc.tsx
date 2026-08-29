import type { ReactNode } from "react";

import { Icon, type IconName } from "@/components/icons";
import { cn } from "@/lib/cn";

/* ---- Segmented control ---------------------------------------------------- */
export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  className,
}: {
  options: readonly { value: T; label: string; icon?: IconName }[];
  value: T;
  onChange: (v: T) => void;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "inline-flex items-center gap-1 rounded-xl border border-line/[0.1] bg-surface-2 p-1",
        className,
      )}
    >
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[13px] font-medium capitalize transition",
              active
                ? "bg-brand/15 text-brand-hi shadow-glow-sm"
                : "text-faint hover:text-content",
            )}
          >
            {opt.icon && <Icon name={opt.icon} size={14} />}
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

/* ---- Page header ------------------------------------------------------------ */
export function PageHeader({
  title,
  subtitle,
  actions,
  className,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "mb-6 flex flex-col gap-3 animate-fade-in-up sm:flex-row sm:items-center sm:justify-between",
        className,
      )}
    >
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-content">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-muted">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

/* ---- Empty state --------------------------------------------------------- */
export function EmptyState({
  icon = "inbox",
  title,
  description,
  action,
  className,
}: {
  icon?: IconName;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "surface-card flex flex-col items-center gap-3 px-6 py-14 text-center",
        className,
      )}
    >
      <div className="grid h-12 w-12 place-items-center rounded-2xl bg-brand/10 text-brand-hi">
        <Icon name={icon} size={22} />
      </div>
      <div>
        <p className="font-semibold text-content">{title}</p>
        {description && <p className="mt-1 text-sm text-muted">{description}</p>}
      </div>
      {action}
    </div>
  );
}

/* ---- Loading ------------------------------------------------------------- */
export function Spinner({ className }: { className?: string }) {
  return <Icon name="refresh" size={18} className={cn("spin text-faint", className)} />;
}

export function Skeleton({ className }: { className?: string }) {
  return (
    <div className={cn("animate-pulse rounded-xl bg-line/[0.06]", className)} />
  );
}

export function LoadingRow({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 py-6 text-sm text-faint">
      <Spinner />
      {label}
    </div>
  );
}

/* ---- Stat tile --------------------------------------------------------- */
export function StatTile({
  label,
  value,
  hint,
  icon,
  tone = "brand",
  className,
}: {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  icon?: IconName;
  tone?: "brand" | "violet" | "amber" | "rose";
  className?: string;
}) {
  const toneCls = {
    brand: "text-brand-hi bg-brand/10",
    violet: "text-violet-300 bg-violet-500/10",
    amber: "text-amber-300 bg-amber-500/10",
    rose: "text-rose-300 bg-rose-500/10",
  }[tone];
  return (
    <div className={cn("surface-card card-hover p-4", className)}>
      <div className="flex items-start justify-between gap-2">
        <span className="label-eyebrow">{label}</span>
        {icon && (
          <span className={cn("grid h-7 w-7 place-items-center rounded-lg", toneCls)}>
            <Icon name={icon} size={15} />
          </span>
        )}
      </div>
      <div className="mt-2 text-2xl font-bold tabular-nums text-content">{value}</div>
      {hint && <div className="mt-0.5 text-xs text-faint">{hint}</div>}
    </div>
  );
}
