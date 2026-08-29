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
        className="h-full w-full max-w-md overflow-y-auto bg-surface p-6 shadow-xl "
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={`${application.role} at ${application.company.name}`}
      >
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h3 className="text-lg font-semibold">{application.role}</h3>
            <p className="text-sm text-muted">{application.company.name}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="text-faint hover:text-content"
          >
            ✕
          </button>
        </div>

        <div className="mb-5">
          <p className="mb-2 text-xs font-medium text-muted">Status</p>
          <div className="flex flex-wrap gap-1.5">
            {STATUS_ORDER.map((status) => (
              <button
                key={status}
                type="button"
                onClick={() => setStatus(status)}
                className={`rounded-full px-2.5 py-1 text-xs font-medium transition ${
                  application.status === status
                    ? STATUS_META[status].badge
                    : "bg-line/[0.08] text-muted hover:bg-line/[0.12] "
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
              className="mt-2 rounded-md border border-line/[0.14] px-3 py-1.5 text-xs font-medium hover:bg-line/[0.08] "
            >
              Edit details
            </button>
          </dl>
        )}

        <div className="mt-6">
          <p className="mb-2 text-xs font-medium text-muted">Interviews</p>
          <ul className="space-y-1.5">
            {application.interviews.map((interview) => (
              <li
                key={interview.id}
                className="flex items-center justify-between rounded-md bg-surface-2 px-3 py-1.5 text-sm "
              >
                <span>
                  {interview.kind}
                  {interview.outcome ? ` · ${interview.outcome}` : ""}
                </span>
                <button
                  type="button"
                  onClick={() => deleteInterview.mutate(interview.id)}
                  aria-label="Remove interview"
                  className="text-faint hover:text-rose-500"
                >
                  ✕
                </button>
              </li>
            ))}
            {application.interviews.length === 0 && (
              <li className="text-sm text-faint">None logged.</li>
            )}
          </ul>
          <form onSubmit={submitInterview} className="mt-2 flex gap-2">
            <input
              value={interviewKind}
              onChange={(event) => setInterviewKind(event.target.value)}
              placeholder="phone, technical, onsite…"
              className="flex-1 rounded-md border border-line/[0.14] bg-surface px-3 py-1.5 text-sm outline-none focus:border-brand/60 focus:ring-4 focus:ring-brand/15"
            />
            <button
              type="submit"
              disabled={addInterview.isPending}
              className="rounded-md btn-primary btn-md disabled:opacity-50"
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
      <dt className="text-muted">{label}</dt>
      <dd className="text-right">{value ?? "–"}</dd>
    </div>
  );
}
