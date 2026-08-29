import { useState } from "react";

import { Modal } from "@/components/Modal";
import {
  Button,
  EmptyState,
  LoadingRow,
  PageHeader,
  SegmentedControl,
} from "@/components/ui";
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

  const selected = applications.find((a) => a.id === selectedId) ?? null;

  return (
    <div>
      <PageHeader
        title="Job Tracker"
        subtitle="Every application, from wishlist to offer."
        actions={
          <>
            <SegmentedControl
              value={view}
              onChange={setView}
              options={[
                { value: "board", label: "board", icon: "kanban" },
                { value: "table", label: "table", icon: "layers" },
              ]}
            />
            <Button variant="primary" icon="plus" onClick={() => setCreating(true)}>
              Application
            </Button>
          </>
        }
      />

      <StatCards />

      <div className="mt-6">
        {isLoading && <LoadingRow />}
        {isError && <p className="text-sm text-rose-400">Could not load applications.</p>}
        {!isLoading && !isError && applications.length === 0 && (
          <EmptyState
            icon="briefcase"
            title="No applications yet"
            description="Add your first one and watch the pipeline fill in."
            action={
              <Button variant="primary" icon="plus" onClick={() => setCreating(true)}>
                Add application
              </Button>
            }
          />
        )}
        {!isLoading && !isError && applications.length > 0 &&
          (view === "board" ? (
            <BoardView applications={applications} onOpen={(a) => setSelectedId(a.id)} />
          ) : (
            <TableView applications={applications} onOpen={(a) => setSelectedId(a.id)} />
          ))}
      </div>

      {creating && (
        <Modal title="New application" onClose={() => setCreating(false)}>
          <ApplicationForm
            showCompany
            submitLabel="Add application"
            pending={create.isPending}
            onSubmit={(input) => create.mutate(input, { onSuccess: () => setCreating(false) })}
          />
        </Modal>
      )}

      {selected && (
        <ApplicationDrawer application={selected} onClose={() => setSelectedId(null)} />
      )}
    </div>
  );
}
