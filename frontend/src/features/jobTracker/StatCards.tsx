import { StatTile } from "@/components/ui";
import { useJobStats } from "@/features/jobTracker/queries";

const pct = (v: number) => `${Math.round(v * 100)}%`;

export function StatCards() {
  const { data } = useJobStats();
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <StatTile label="Total" value={data ? data.total : "–"} icon="briefcase" />
      <StatTile label="Active" value={data ? data.active : "–"} icon="clock" tone="violet" />
      <StatTile
        label="Response rate"
        value={data ? pct(data.response_rate) : "–"}
        icon="chart"
        tone="amber"
      />
      <StatTile label="Offers" value={data ? data.offers : "–"} icon="target" />
    </div>
  );
}
