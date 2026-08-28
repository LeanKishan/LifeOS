import type { Application } from "@/features/jobTracker/api";
import { STATUS_META, STATUS_ORDER, formatSalary } from "@/features/jobTracker/statusMeta";

export function BoardView({
  applications,
  onOpen,
}: {
  applications: Application[];
  onOpen: (application: Application) => void;
}) {
  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {STATUS_ORDER.map((status) => {
        const items = applications.filter((application) => application.status === status);
        return (
          <div key={status} className="w-64 shrink-0">
            <div className="mb-2 flex items-center gap-2 text-sm font-medium">
              <span className={`h-2 w-2 rounded-full ${STATUS_META[status].dot}`} />
              {STATUS_META[status].label}
              <span className="text-slate-400">{items.length}</span>
            </div>
            <div className="space-y-2">
              {items.map((application) => {
                const salary = formatSalary(application);
                return (
                  <button
                    key={application.id}
                    type="button"
                    onClick={() => onOpen(application)}
                    className="block w-full rounded-lg border border-slate-200 bg-white p-3 text-left text-sm hover:border-emerald-400 dark:border-slate-800 dark:bg-slate-900"
                  >
                    <div className="font-medium">{application.role}</div>
                    <div className="text-slate-500">{application.company.name}</div>
                    {salary && <div className="mt-1 text-xs text-slate-400">{salary}</div>}
                    {application.interviews.length > 0 && (
                      <div className="mt-1 text-xs text-slate-400">
                        {application.interviews.length} interview
                        {application.interviews.length > 1 ? "s" : ""}
                      </div>
                    )}
                  </button>
                );
              })}
              {items.length === 0 && (
                <p className="rounded-lg border border-dashed border-slate-200 p-3 text-center text-xs text-slate-400 dark:border-slate-800">
                  Nothing here
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
