import type { Tone } from "@/components/ui";
import type { ApplicationStatus } from "@/features/jobTracker/api";

interface StatusMeta {
  label: string;
  dot: string;
  tone: Tone;
  /** ready-to-use pill classes (pill base + tone) for non-<Badge> spots */
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

const B = (tone: string) => `pill ${tone}`;

export const STATUS_META: Record<ApplicationStatus, StatusMeta> = {
  wishlist: { label: "Wishlist", dot: "bg-slate-400", tone: "neutral", badge: B("bg-line/[0.06] text-muted ring-line/10") },
  applied: { label: "Applied", dot: "bg-blue-400", tone: "blue", badge: B("bg-blue-500/12 text-blue-300 ring-blue-500/20") },
  assessment: { label: "Assessment", dot: "bg-violet-400", tone: "violet", badge: B("bg-violet-500/12 text-violet-300 ring-violet-500/20") },
  interviewing: { label: "Interviewing", dot: "bg-amber-400", tone: "amber", badge: B("bg-amber-500/12 text-amber-300 ring-amber-500/20") },
  offer: { label: "Offer", dot: "bg-brand-hi", tone: "brand", badge: B("bg-brand/10 text-brand-hi ring-brand/20") },
  accepted: { label: "Accepted", dot: "bg-emerald-400", tone: "emerald", badge: B("bg-brand/12 text-emerald-300 ring-emerald-500/20") },
  rejected: { label: "Rejected", dot: "bg-rose-400", tone: "rose", badge: B("bg-rose-500/12 text-rose-300 ring-rose-500/20") },
  withdrawn: { label: "Withdrawn", dot: "bg-slate-500", tone: "neutral", badge: B("bg-line/[0.06] text-faint ring-line/10") },
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
