import type { ApplicationStatus } from "@/features/jobTracker/api";

interface StatusMeta {
  label: string;
  dot: string;
  badge: string;
}

export const STATUS_ORDER: ApplicationStatus[] = [
  "wishlist",
  "applied",
  "assessment",
  "interviewing",
  "offer",
  "accepted",
  "rejected",
  "withdrawn",
];

export const STATUS_META: Record<ApplicationStatus, StatusMeta> = {
  wishlist: {
    label: "Wishlist",
    dot: "bg-slate-400",
    badge: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  },
  applied: {
    label: "Applied",
    dot: "bg-blue-500",
    badge: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
  },
  assessment: {
    label: "Assessment",
    dot: "bg-violet-500",
    badge: "bg-violet-100 text-violet-700 dark:bg-violet-950 dark:text-violet-300",
  },
  interviewing: {
    label: "Interviewing",
    dot: "bg-amber-500",
    badge: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  },
  offer: {
    label: "Offer",
    dot: "bg-emerald-500",
    badge: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
  },
  accepted: {
    label: "Accepted",
    dot: "bg-emerald-600",
    badge: "bg-emerald-200 text-emerald-900 dark:bg-emerald-900 dark:text-emerald-200",
  },
  rejected: {
    label: "Rejected",
    dot: "bg-rose-500",
    badge: "bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300",
  },
  withdrawn: {
    label: "Withdrawn",
    dot: "bg-slate-400",
    badge: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400",
  },
};

export function formatSalary(app: {
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string;
}): string | null {
  const { salary_min, salary_max, salary_currency } = app;
  if (salary_min == null && salary_max == null) return null;
  const fmt = (n: number) => `${salary_currency} ${Math.round(n / 1000)}k`;
  if (salary_min != null && salary_max != null) return `${fmt(salary_min)}–${fmt(salary_max)}`;
  return fmt((salary_min ?? salary_max) as number);
}
