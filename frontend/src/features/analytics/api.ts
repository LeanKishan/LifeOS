import { api } from "@/lib/api";

export interface WeekPoint {
  week: string;
  count: number;
}

export interface MonthPoint {
  month: string;
  income_cents: number;
  expense_cents: number;
  net_cents: number;
}

export interface NamedAmount {
  name: string;
  spent_cents: number;
}

export interface AnalyticsOverview {
  range: { date_from: string; date_to: string };
  productivity: {
    tasks_total: number;
    tasks_done: number;
    completion_rate: number;
    avg_cycle_days: number | null;
    overdue: number;
    by_priority: Record<string, number>;
    done_by_week: WeekPoint[];
  };
  finance: {
    by_month: MonthPoint[];
    top_categories: NamedAmount[];
  };
  learning: {
    cards_total: number;
    reviews_last_7d: number;
    maturity: Record<string, number>;
    lessons_done_by_week: WeekPoint[];
  };
  job_search: {
    funnel: Record<string, number>;
    applications_by_week: WeekPoint[];
  };
}

export async function getOverview(from: string, to: string): Promise<AnalyticsOverview> {
  const { data } = await api.get<AnalyticsOverview>("/analytics/overview", {
    params: { from, to },
  });
  return data;
}

export async function fetchExport(kind: "csv" | "pdf", from: string, to: string): Promise<Blob> {
  const { data } = await api.get(`/analytics/export.${kind}`, {
    params: { from, to },
    responseType: "blob",
  });
  return data as Blob;
}
