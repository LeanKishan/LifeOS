import { useJobStats } from "@/features/jobTracker/queries";

function pct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function StatCards() {
  const { data } = useJobStats();

  const cards = [
    { label: "Total", value: data ? data.total : "–" },
    { label: "Active", value: data ? data.active : "–" },
    { label: "Response rate", value: data ? pct(data.response_rate) : "–" },
    { label: "Offers", value: data ? data.offers : "–" },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"
        >
          <div className="text-2xl font-bold tabular-nums">{card.value}</div>
          <div className="text-xs text-slate-500">{card.label}</div>
        </div>
      ))}
    </div>
  );
}
