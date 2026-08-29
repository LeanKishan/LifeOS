import { Icon } from "@/components/icons";
import type { Application } from "@/features/jobTracker/api";
import { STATUS_META, formatSalary } from "@/features/jobTracker/statusMeta";

export function TableView({
  applications,
  onOpen,
}: {
  applications: Application[];
  onOpen: (application: Application) => void;
}) {
  if (applications.length === 0) {
    return <p className="text-sm text-muted">No applications yet.</p>;
  }

  return (
    <div className="surface-card overflow-hidden p-0">
      {/* mobile: cards */}
      <ul className="divide-y divide-line/[0.05] md:hidden">
        {applications.map((a) => (
          <li key={a.id}>
            <button
              type="button"
              onClick={() => onOpen(a)}
              className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left transition hover:bg-line/[0.03]"
            >
              <div className="min-w-0">
                <div className="truncate font-medium text-content">{a.role}</div>
                <div className="truncate text-xs text-faint">
                  {a.company.name}
                  {formatSalary(a) ? ` · ${formatSalary(a)}` : ""}
                </div>
              </div>
              <span className={`${STATUS_META[a.status].badge} shrink-0`}>
                {STATUS_META[a.status].label}
              </span>
            </button>
          </li>
        ))}
      </ul>

      {/* desktop: table */}
      <table className="hidden w-full text-left text-sm md:table">
        <thead>
          <tr className="border-b border-line/[0.08] text-xs uppercase tracking-wide text-faint">
            <th className="px-4 py-3 font-semibold">Company</th>
            <th className="px-4 py-3 font-semibold">Role</th>
            <th className="px-4 py-3 font-semibold">Status</th>
            <th className="px-4 py-3 font-semibold">Source</th>
            <th className="px-4 py-3 font-semibold">Salary</th>
            <th className="px-4 py-3 font-semibold">Applied</th>
          </tr>
        </thead>
        <tbody>
          {applications.map((a) => (
            <tr
              key={a.id}
              onClick={() => onOpen(a)}
              className="cursor-pointer border-b border-line/[0.05] last:border-0 transition hover:bg-line/[0.03]"
            >
              <td className="px-4 py-2.5 font-medium text-content">{a.company.name}</td>
              <td className="px-4 py-2.5 text-muted">{a.role}</td>
              <td className="px-4 py-2.5">
                <span className={STATUS_META[a.status].badge}>{STATUS_META[a.status].label}</span>
              </td>
              <td className="px-4 py-2.5 text-muted">{a.source ?? "–"}</td>
              <td className="px-4 py-2.5 tabular-nums text-muted">{formatSalary(a) ?? "–"}</td>
              <td className="px-4 py-2.5 tabular-nums text-muted">
                <span className="flex items-center gap-1">
                  {a.applied_on ? <Icon name="calendar" size={12} /> : null}
                  {a.applied_on ?? "–"}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
