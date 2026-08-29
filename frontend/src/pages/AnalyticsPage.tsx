import { useMemo, useState } from "react";

import { Button, LoadingRow, PageHeader, SegmentedControl, StatTile } from "@/components/ui";
import { fetchExport } from "@/features/analytics/api";
import {
  Bars,
  ChartCard,
  DivergingBars,
  Donut,
  Section,
  SERIES,
  StackedBar,
  TrendLine,
  type Slice,
} from "@/features/analytics/charts";
import { useOverview } from "@/features/analytics/queries";
import { formatCents } from "@/features/finance/money";

const RANGES = [
  { label: "30 days", days: 30 },
  { label: "90 days", days: 90 },
  { label: "1 year", days: 365 },
];

const PRIORITY_COLOR: Record<string, string> = {
  urgent: SERIES[4],
  high: SERIES[2],
  medium: SERIES[1],
  low: SERIES[5],
};
const MATURITY_COLOR: Record<string, string> = {
  new: SERIES[5],
  learning: SERIES[1],
  young: SERIES[6],
  mature: SERIES[0],
};
const FUNNEL_STAGES = [
  "wishlist",
  "applied",
  "assessment",
  "interviewing",
  "offer",
  "accepted",
  "rejected",
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

  const prioritySlices: Slice[] = data
    ? ["urgent", "high", "medium", "low"].map((p) => ({
        label: p,
        value: data.productivity.by_priority[p] ?? 0,
        color: PRIORITY_COLOR[p],
      }))
    : [];
  const maturitySlices: Slice[] = data
    ? ["new", "learning", "young", "mature"].map((k) => ({
        label: k,
        value: data.learning.maturity[k] ?? 0,
        color: MATURITY_COLOR[k],
      }))
    : [];
  const funnelSlices: Slice[] = data
    ? FUNNEL_STAGES.map((s, i) => ({
        label: s,
        value: data.job_search.funnel[s] ?? 0,
        color: SERIES[i % SERIES.length],
      }))
    : [];

  const TILE_ICON = ["target", "clock", "flag", "book"] as const;

  return (
    <div>
      <PageHeader
        title="Analytics"
        subtitle="Cross-module trends over your chosen window."
        actions={
          <>
            <SegmentedControl
              value={String(days)}
              onChange={(v) => setDays(Number(v))}
              options={RANGES.map((r) => ({ value: String(r.days), label: r.label }))}
            />
            <Button variant="secondary" icon="download" onClick={() => void download("csv")}>
              CSV
            </Button>
            <Button variant="secondary" icon="download" onClick={() => void download("pdf")}>
              PDF
            </Button>
          </>
        }
      />

      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {tiles.map((tile, i) => (
          <StatTile
            key={tile.label}
            label={tile.label}
            value={tile.value}
            icon={TILE_ICON[i]}
            tone={(["brand", "violet", "amber", "rose"] as const)[i]}
          />
        ))}
      </div>

      {isLoading && <LoadingRow />}

      {data && (
        <>
          <Section title="Productivity">
            <ChartCard title="Tasks completed per week">
              <TrendLine
                data={data.productivity.done_by_week.map((p) => ({
                  label: weekLabel(p.week),
                  value: p.count,
                }))}
              />
            </ChartCard>
            <ChartCard title="Open tasks by priority">
              <Donut data={prioritySlices} />
            </ChartCard>
          </Section>

          <Section title="Finance">
            <ChartCard title="Net by month">
              <DivergingBars
                data={data.finance.by_month.map((m) => ({
                  label: m.month.slice(2),
                  value: m.net_cents,
                }))}
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
          </Section>

          <Section title="Learning">
            <ChartCard title="Lessons completed per week">
              <TrendLine
                data={data.learning.lessons_done_by_week.map((p) => ({
                  label: weekLabel(p.week),
                  value: p.count,
                }))}
              />
            </ChartCard>
            <ChartCard title="Flashcard maturity">
              <StackedBar segments={maturitySlices} />
            </ChartCard>
          </Section>

          <Section title="Job search">
            <ChartCard title="Application funnel">
              <StackedBar segments={funnelSlices} />
            </ChartCard>
            <ChartCard title="Applications per week">
              <TrendLine
                data={data.job_search.applications_by_week.map((p) => ({
                  label: weekLabel(p.week),
                  value: p.count,
                }))}
              />
            </ChartCard>
          </Section>
        </>
      )}
    </div>
  );
}
