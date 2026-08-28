import { useState } from "react";

import { Modal } from "@/components/Modal";
import { ApplicationDrawer } from "@/features/jobTracker/ApplicationDrawer";
import { ApplicationForm } from "@/features/jobTracker/ApplicationForm";
import { BoardView } from "@/features/jobTracker/BoardView";
import { StatCards } from "@/features/jobTracker/StatCards";
import { TableView } from "@/features/jobTracker/TableView";
import { useApplications, useCreateApplication } from "@/features/jobTracker/queries";

type View = "board" | "table";

export default function JobTrackerPage() {
  const [view, setView] = useState<View>("board");
  const [creating, setCreating] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const { data: applications = [], isLoading, isError } = useApplications({ sort: "-created_at" });
  const create = useCreateApplication();

  const selected = applications.find((application) => application.id === selectedId) ?? null;

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-semibold">Job Tracker</h2>
        <div className="flex items-center gap-2">
          <div className="flex rounded-md border border-slate-300 text-sm dark:border-slate-700">
            {(["board", "table"] as const).map((value) => (
              <button
                key={value}
                type="button"
                onClick={() => setView(value)}
                className={`px-3 py-1.5 capitalize ${
                  view === value
                    ? "bg-slate-100 font-medium dark:bg-slate-800"
                    : "text-slate-500"
                }`}
              >
                {value}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={() => setCreating(true)}
            className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700"
          >
            + Application
          </button>
        </div>
      </div>

      <StatCards />

      <div className="mt-6">
        {isLoading && <p className="text-sm text-slate-500">Loading…</p>}
        {isError && <p className="text-sm text-rose-600">Could not load applications.</p>}
        {!isLoading && !isError && (
          <>
            {applications.length === 0 && (
              <p className="text-sm text-slate-500">
                No applications yet — add your first one.
              </p>
            )}
            {applications.length > 0 &&
              (view === "board" ? (
                <BoardView applications={applications} onOpen={(a) => setSelectedId(a.id)} />
              ) : (
                <TableView applications={applications} onOpen={(a) => setSelectedId(a.id)} />
              ))}
          </>
        )}
      </div>

      {creating && (
        <Modal title="New application" onClose={() => setCreating(false)}>
          <ApplicationForm
            showCompany
            submitLabel="Add application"
            pending={create.isPending}
            onSubmit={(input) =>
              create.mutate(input, { onSuccess: () => setCreating(false) })
            }
          />
        </Modal>
      )}

      {selected && (
        <ApplicationDrawer application={selected} onClose={() => setSelectedId(null)} />
      )}
    </div>
  );
}
