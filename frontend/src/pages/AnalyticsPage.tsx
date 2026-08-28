import { useMemo, useState } from "react";

import { fetchExport } from "@/features/analytics/api";
import { Bars, ChartCard, DivergingBars } from "@/features/analytics/charts";
import { useOverview } from "@/features/analytics/queries";
import { formatCents } from "@/features/finance/money";

const RANGES = [
  { label: "30 days", days: 30 },
  { label: "90 days", days: 90 },
  { label: "1 year", days: 365 },
];

function isoDaysAgo(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10);
}

function weekLabel(iso: string): string {
  return iso.slice(5); // MM-DD
}

export default function AnalyticsPage() {
  const [days, setDays] = useState(90);
  const from = useMemo(() => isoDaysAgo(days), [days]);
  const to = useMemo(() => new Date().toISOString().slice(0, 10), []);
  const { data, isLoading } = useOverview(from, to);

  async function download(kind: "csv" | "pdf"): Promise<void> {
    const blob = await fetchExport(kind, from, to);
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `lifeos-analytics.${kind}`;
    link.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
  }

  const tiles = [
    {
      label: "Completion rate",
      value: data ? `${Math.round(data.productivity.completion_rate * 100)}%` : "–",
    },
    {
      label: "Avg cycle (days)",
      value:
        data && data.productivity.avg_cycle_days !== null
          ? data.productivity.avg_cycle_days
          : "–",
    },
    { label: "Overdue", value: data ? data.productivity.overdue : "–" },
    { label: "Mature cards", value: data ? data.learning.maturity.mature : "–" },
  ];

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-semibold">Analytics</h2>
        <div className="flex items-center gap-2">
          <div className="flex rounded-md border border-slate-300 text-sm dark:border-slate-700">
            {RANGES.map((range) => (
              <button
                key={range.days}
                type="button"
                onClick={() => setDays(range.days)}
                className={`px-3 py-1.5 ${
                  days === range.days ? "bg-slate-100 font-medium dark:bg-slate-800" : "text-slate-500"
                }`}
              >
                {range.label}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={() => void download("csv")}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            CSV
          </button>
          <button
            type="button"
            onClick={() => void download("pdf")}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            PDF
          </button>
        </div>
      </div>

      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {tiles.map((tile) => (
          <div
            key={tile.label}
            className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="text-xl font-bold tabular-nums">{tile.value}</div>
            <div className="text-xs text-slate-500">{tile.label}</div>
          </div>
        ))}
      </div>

      {isLoading && <p className="text-sm text-slate-500">Loading…</p>}

      {data && (
        <div className="grid gap-4 lg:grid-cols-2">
          <ChartCard title="Tasks completed per week">
            <Bars
              data={data.productivity.done_by_week.map((p) => ({
                label: weekLabel(p.week),
                value: p.count,
              }))}
            />
          </ChartCard>

          <ChartCard title="Open tasks by priority">
            <Bars
              data={["urgent", "high", "medium", "low"].map((p) => ({
                label: p,
                value: data.productivity.by_priority[p] ?? 0,
              }))}
            />
          </ChartCard>

          <ChartCard title="Net by month">
            <DivergingBars
              data={data.finance.by_month.map((m) => ({ label: m.month.slice(2), value: m.net_cents }))}
              format={formatCents}
            />
          </ChartCard>

          <ChartCard title="Top spending">
            <Bars
              data={data.finance.top_categories.map((c) => ({
                label: c.name,
                value: c.spent_cents,
              }))}
              format={formatCents}
            />
          </ChartCard>

          <ChartCard title="Flashcard maturity">
            <Bars
              data={["new", "learning", "young", "mature"].map((k) => ({
                label: k,
                value: data.learning.maturity[k] ?? 0,
              }))}
            />
          </ChartCard>

          <ChartCard title="Application funnel">
            <Bars
              data={["wishlist", "applied", "assessment", "interviewing", "offer", "accepted", "rejected"].map(
                (s) => ({ label: s, value: data.job_search.funnel[s] ?? 0 }),
              )}
            />
          </ChartCard>
        </div>
      )}
    </div>
  );
}
