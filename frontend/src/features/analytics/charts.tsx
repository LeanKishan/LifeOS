import type { ReactNode } from "react";

export interface Datum {
  label: string;
  value: number;
}

export interface Slice {
  label: string;
  value: number;
  color: string;
}

/** A categorical palette reused across the multi-series charts. */
export const SERIES = [
  "#10b981",
  "#3b82f6",
  "#f59e0b",
  "#8b5cf6",
  "#ef4444",
  "#64748b",
  "#14b8a6",
  "#ec4899",
];

const empty = <p className="text-xs text-faint">No data in this range.</p>;

export function Bars({
  data,
  format = String,
}: {
  data: Datum[];
  format?: (value: number) => string;
}) {
  const max = Math.max(1, ...data.map((d) => d.value));
  if (data.every((d) => d.value === 0)) return empty;
  return (
    <div className="space-y-1.5">
      {data.map((d) => (
        <div key={d.label} className="flex items-center gap-2 text-xs">
          <span className="w-24 shrink-0 truncate text-muted">{d.label}</span>
          <div className="h-3 flex-1 rounded bg-line/[0.08]">
            <div
              className="h-3 rounded bg-brand"
              style={{ width: `${(d.value / max) * 100}%` }}
            />
          </div>
          <span className="w-16 shrink-0 text-right tabular-nums">{format(d.value)}</span>
        </div>
      ))}
    </div>
  );
}

export function DivergingBars({
  data,
  format = String,
}: {
  data: Datum[];
  format?: (value: number) => string;
}) {
  const max = Math.max(1, ...data.map((d) => Math.abs(d.value)));
  if (data.length === 0) return empty;
  return (
    <div className="space-y-1.5">
      {data.map((d) => {
        const pct = (Math.abs(d.value) / max) * 50;
        const positive = d.value >= 0;
        return (
          <div key={d.label} className="flex items-center gap-2 text-xs">
            <span className="w-16 shrink-0 text-muted">{d.label}</span>
            <div className="relative h-3 flex-1 rounded bg-line/[0.08]">
              <div className="absolute left-1/2 top-0 h-3 w-px bg-line/20" />
              <div
                className={`absolute top-0 h-3 ${
                  positive ? "left-1/2 rounded-r bg-brand" : "right-1/2 rounded-l bg-rose-500"
                }`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <span
              className={`w-20 shrink-0 text-right tabular-nums ${positive ? "" : "text-rose-400"}`}
            >
              {format(d.value)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

/** Inline SVG trend line with an area fill and a marker on the latest point. */
export function TrendLine({
  data,
  format = String,
}: {
  data: Datum[];
  format?: (value: number) => string;
}) {
  const points = data.filter((d) => Number.isFinite(d.value));
  if (points.length < 2) {
    return <p className="text-xs text-faint">Not enough history yet.</p>;
  }

  const values = points.map((d) => d.value);
  const max = Math.max(1, ...values);
  const w = 100;
  const h = 32;
  const pad = 2;
  const x = (i: number) => pad + (i / (points.length - 1)) * (w - 2 * pad);
  const y = (v: number) => h - pad - (v / max) * (h - 2 * pad);

  const line = points.map((d, i) => `${x(i).toFixed(1)},${y(d.value).toFixed(1)}`).join(" ");
  const area = `${x(0).toFixed(1)},${h - pad} ${line} ${x(points.length - 1).toFixed(1)},${h - pad}`;
  const last = points[points.length - 1]!;
  const peak = Math.max(...values);

  return (
    <div>
      <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" className="h-16 w-full">
        <polygon points={area} className="fill-brand/15" />
        <polyline
          points={line}
          fill="none"
          className="stroke-brand-hi"
          strokeWidth={1.5}
          strokeLinejoin="round"
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
        />
        <circle cx={x(points.length - 1)} cy={y(last.value)} r={2} className="fill-brand-hi" />
      </svg>
      <div className="mt-1 flex justify-between text-[11px] text-faint">
        <span>{points[0]!.label}</span>
        <span className="tabular-nums text-muted">
          {format(last.value)} · {last.label} · peak {format(peak)}
        </span>
      </div>
    </div>
  );
}

/** One horizontal bar split into proportional segments, with a legend. */
export function StackedBar({ segments }: { segments: Slice[] }) {
  const total = segments.reduce((sum, s) => sum + s.value, 0);
  if (total === 0) return empty;
  return (
    <div>
      <div className="flex h-4 w-full overflow-hidden rounded bg-line/[0.08]">
        {segments
          .filter((s) => s.value > 0)
          .map((s) => (
            <div
              key={s.label}
              style={{ width: `${(s.value / total) * 100}%`, backgroundColor: s.color }}
              title={`${s.label}: ${s.value}`}
            />
          ))}
      </div>
      <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-muted">
        {segments.map((s) => (
          <span key={s.label} className="flex items-center gap-1">
            <span
              className="inline-block h-2 w-2 rounded-sm"
              style={{ backgroundColor: s.color }}
            />
            {s.label} <span className="tabular-nums text-faint">{s.value}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

/** SVG donut for a small set of proportions. */
export function Donut({ data }: { data: Slice[] }) {
  const total = data.reduce((sum, d) => sum + d.value, 0);
  if (total === 0) return empty;

  const r = 15.915; // circumference ≈ 100
  const circ = 2 * Math.PI * r;
  let offset = 0;

  return (
    <div className="flex items-center gap-4">
      <svg viewBox="0 0 40 40" className="h-24 w-24 -rotate-90">
        <circle
          cx={20}
          cy={20}
          r={r}
          fill="none"
          strokeWidth={5}
          className="stroke-line/10"
        />
        {data
          .filter((d) => d.value > 0)
          .map((d) => {
            const len = (d.value / total) * circ;
            const seg = (
              <circle
                key={d.label}
                cx={20}
                cy={20}
                r={r}
                fill="none"
                stroke={d.color}
                strokeWidth={5}
                strokeDasharray={`${len.toFixed(2)} ${(circ - len).toFixed(2)}`}
                strokeDashoffset={(-offset).toFixed(2)}
              />
            );
            offset += len;
            return seg;
          })}
      </svg>
      <div className="space-y-1 text-[11px]">
        {data.map((d) => (
          <div key={d.label} className="flex items-center gap-1.5 text-muted">
            <span
              className="inline-block h-2 w-2 rounded-sm"
              style={{ backgroundColor: d.color }}
            />
            {d.label}
            <span className="tabular-nums text-faint">
              {total ? Math.round((d.value / total) * 100) : 0}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="mb-6">
      <h3 className="mb-2 label-eyebrow">
        {title}
      </h3>
      <div className="grid gap-4 lg:grid-cols-2">{children}</div>
    </section>
  );
}

export function ChartCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="surface-card card-hover p-5">
      <h4 className="mb-4 text-sm font-semibold text-muted">{title}</h4>
      {children}
    </div>
  );
}
