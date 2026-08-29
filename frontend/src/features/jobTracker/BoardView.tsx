import { Icon } from "@/components/icons";
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
        const items = applications.filter((a) => a.status === status);
        return (
          <div
            key={status}
            className="flex w-64 shrink-0 flex-col rounded-2xl border border-line/[0.06] bg-line/[0.02] p-2"
          >
            <div className="mb-2 flex items-center gap-2 px-1.5 py-1 text-[13px] font-semibold text-content">
              <span className={`h-1.5 w-1.5 rounded-full ${STATUS_META[status].dot}`} />
              {STATUS_META[status].label}
              <span className="ml-auto rounded-md bg-line/[0.06] px-1.5 text-xs text-faint">
                {items.length}
              </span>
            </div>
            <div className="space-y-2">
              {items.map((application) => {
                const salary = formatSalary(application);
                return (
                  <button
                    key={application.id}
                    type="button"
                    onClick={() => onOpen(application)}
                    className="block w-full rounded-xl border border-line/[0.08] bg-elev p-3 text-left text-sm shadow-card transition hover:-translate-y-0.5 hover:border-brand/40"
                  >
                    <div className="font-medium text-content">{application.role}</div>
                    <div className="text-muted">{application.company.name}</div>
                    {salary && (
                      <div className="mt-1.5 flex items-center gap-1 text-xs text-faint">
                        <Icon name="wallet" size={12} />
                        {salary}
                      </div>
                    )}
                    {application.interviews.length > 0 && (
                      <div className="mt-1 flex items-center gap-1 text-xs text-faint">
                        <Icon name="user" size={12} />
                        {application.interviews.length} interview
                        {application.interviews.length > 1 ? "s" : ""}
                      </div>
                    )}
                  </button>
                );
              })}
              {items.length === 0 && (
                <p className="rounded-xl border border-dashed border-line/[0.1] p-3 text-center text-xs text-faint">
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
