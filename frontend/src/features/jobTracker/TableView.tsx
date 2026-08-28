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
    return <p className="text-sm text-slate-500">No applications yet.</p>;
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-50 text-xs uppercase text-slate-500 dark:bg-slate-900">
          <tr>
            <th className="px-4 py-2">Company</th>
            <th className="px-4 py-2">Role</th>
            <th className="px-4 py-2">Status</th>
            <th className="px-4 py-2">Source</th>
            <th className="px-4 py-2">Salary</th>
            <th className="px-4 py-2">Applied</th>
          </tr>
        </thead>
        <tbody>
          {applications.map((application) => (
            <tr
              key={application.id}
              onClick={() => onOpen(application)}
              className="cursor-pointer border-t border-slate-200 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-900"
            >
              <td className="px-4 py-2 font-medium">{application.company.name}</td>
              <td className="px-4 py-2">{application.role}</td>
              <td className="px-4 py-2">
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_META[application.status].badge}`}
                >
                  {STATUS_META[application.status].label}
                </span>
              </td>
              <td className="px-4 py-2 text-slate-500">{application.source ?? "–"}</td>
              <td className="px-4 py-2 text-slate-500">{formatSalary(application) ?? "–"}</td>
              <td className="px-4 py-2 text-slate-500">{application.applied_on ?? "–"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
