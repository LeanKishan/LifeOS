export interface Datum {
  label: string;
  value: number;
}

export function Bars({
  data,
  format = String,
}: {
  data: Datum[];
  format?: (value: number) => string;
}) {
  const max = Math.max(1, ...data.map((d) => d.value));
  if (data.every((d) => d.value === 0)) {
    return <p className="text-xs text-slate-400">No data in this range.</p>;
  }
  return (
    <div className="space-y-1.5">
      {data.map((d) => (
        <div key={d.label} className="flex items-center gap-2 text-xs">
          <span className="w-24 shrink-0 truncate text-slate-500">{d.label}</span>
          <div className="h-3 flex-1 rounded bg-slate-100 dark:bg-slate-800">
            <div
              className="h-3 rounded bg-emerald-500"
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
  if (data.length === 0) {
    return <p className="text-xs text-slate-400">No data in this range.</p>;
  }
  return (
    <div className="space-y-1.5">
      {data.map((d) => {
        const pct = (Math.abs(d.value) / max) * 50;
        const positive = d.value >= 0;
        return (
          <div key={d.label} className="flex items-center gap-2 text-xs">
            <span className="w-16 shrink-0 text-slate-500">{d.label}</span>
            <div className="relative h-3 flex-1 rounded bg-slate-100 dark:bg-slate-800">
              <div className="absolute left-1/2 top-0 h-3 w-px bg-slate-300 dark:bg-slate-600" />
              <div
                className={`absolute top-0 h-3 ${
                  positive ? "left-1/2 rounded-r bg-emerald-500" : "right-1/2 rounded-l bg-rose-500"
                }`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <span
              className={`w-20 shrink-0 text-right tabular-nums ${positive ? "" : "text-rose-600"}`}
            >
              {format(d.value)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export function ChartCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <h3 className="mb-3 text-sm font-medium text-slate-500">{title}</h3>
      {children}
    </div>
  );
}
