import { useState, type FormEvent } from "react";

import type { Application } from "@/features/jobTracker/api";
import { ApplicationForm } from "@/features/jobTracker/ApplicationForm";
import {
  useAddInterview,
  useDeleteApplication,
  useDeleteInterview,
  useUpdateApplication,
} from "@/features/jobTracker/queries";
import { STATUS_META, STATUS_ORDER, formatSalary } from "@/features/jobTracker/statusMeta";

export function ApplicationDrawer({
  application,
  onClose,
}: {
  application: Application;
  onClose: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [interviewKind, setInterviewKind] = useState("");

  const update = useUpdateApplication();
  const remove = useDeleteApplication();
  const addInterview = useAddInterview();
  const deleteInterview = useDeleteInterview();

  function setStatus(status: Application["status"]): void {
    update.mutate({ id: application.id, input: { status } });
  }

  function submitInterview(event: FormEvent): void {
    event.preventDefault();
    const kind = interviewKind.trim();
    if (!kind) return;
    addInterview.mutate(
      { applicationId: application.id, input: { kind } },
      { onSuccess: () => setInterviewKind("") },
    );
  }

  function handleDelete(): void {
    remove.mutate(application.id, { onSuccess: onClose });
  }

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end bg-black/40"
      onClick={onClose}
      role="presentation"
    >
      <aside
        className="h-full w-full max-w-md overflow-y-auto bg-white p-6 shadow-xl dark:bg-slate-900"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={`${application.role} at ${application.company.name}`}
      >
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h3 className="text-lg font-semibold">{application.role}</h3>
            <p className="text-sm text-slate-500">{application.company.name}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
          >
            ✕
          </button>
        </div>

        <div className="mb-5">
          <p className="mb-2 text-xs font-medium text-slate-500">Status</p>
          <div className="flex flex-wrap gap-1.5">
            {STATUS_ORDER.map((status) => (
              <button
                key={status}
                type="button"
                onClick={() => setStatus(status)}
                className={`rounded-full px-2.5 py-1 text-xs font-medium transition ${
                  application.status === status
                    ? STATUS_META[status].badge
                    : "bg-slate-100 text-slate-500 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700"
                }`}
              >
                {STATUS_META[status].label}
              </button>
            ))}
          </div>
        </div>

        {editing ? (
          <ApplicationForm
            showCompany={false}
            submitLabel="Save changes"
            pending={update.isPending}
            initial={{
              role: application.role,
              status: application.status,
              source: application.source,
              location: application.location,
              job_url: application.job_url,
              salary_min: application.salary_min,
              salary_max: application.salary_max,
              applied_on: application.applied_on,
              notes: application.notes,
            }}
            onSubmit={(input) =>
              update.mutate(
                { id: application.id, input },
                { onSuccess: () => setEditing(false) },
              )
            }
          />
        ) : (
          <dl className="space-y-1.5 text-sm">
            <Detail label="Source" value={application.source} />
            <Detail label="Location" value={application.location} />
            <Detail label="Salary" value={formatSalary(application)} />
            <Detail label="Applied on" value={application.applied_on} />
            <Detail label="Job URL" value={application.job_url} />
            <Detail label="Notes" value={application.notes} />
            <button
              type="button"
              onClick={() => setEditing(true)}
              className="mt-2 rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
            >
              Edit details
            </button>
          </dl>
        )}

        <div className="mt-6">
          <p className="mb-2 text-xs font-medium text-slate-500">Interviews</p>
          <ul className="space-y-1.5">
            {application.interviews.map((interview) => (
              <li
                key={interview.id}
                className="flex items-center justify-between rounded-md bg-slate-50 px-3 py-1.5 text-sm dark:bg-slate-800"
              >
                <span>
                  {interview.kind}
                  {interview.outcome ? ` · ${interview.outcome}` : ""}
                </span>
                <button
                  type="button"
                  onClick={() => deleteInterview.mutate(interview.id)}
                  aria-label="Remove interview"
                  className="text-slate-400 hover:text-rose-500"
                >
                  ✕
                </button>
              </li>
            ))}
            {application.interviews.length === 0 && (
              <li className="text-sm text-slate-400">None logged.</li>
            )}
          </ul>
          <form onSubmit={submitInterview} className="mt-2 flex gap-2">
            <input
              value={interviewKind}
              onChange={(event) => setInterviewKind(event.target.value)}
              placeholder="phone, technical, onsite…"
              className="flex-1 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm outline-none focus:border-emerald-500 dark:border-slate-700 dark:bg-slate-900"
            />
            <button
              type="submit"
              disabled={addInterview.isPending}
              className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              Add
            </button>
          </form>
        </div>

        <button
          type="button"
          onClick={handleDelete}
          className="mt-8 text-xs font-medium text-rose-600 hover:underline"
        >
          Delete this application
        </button>
      </aside>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-slate-500">{label}</dt>
      <dd className="text-right">{value ?? "–"}</dd>
    </div>
  );
}
