import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

export interface WeekPoint {
  week: string;
  count: number;
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
    by_month: { month: string; income_cents: number; expense_cents: number; net_cents: number }[];
    top_categories: { name: string; spent_cents: number }[];
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

export function useOverview() {
  return useQuery({
    queryKey: ["analytics", "overview"],
    queryFn: async () => {
      const { data } = await api.get<AnalyticsOverview>("/analytics/overview");
      return data;
    },
  });
}
