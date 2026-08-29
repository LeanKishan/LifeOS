import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Icon } from "@/components/icons";
import { Button, LoadingRow, PageHeader } from "@/components/ui";
import * as pj from "@/features/projects/api";
import { KanbanBoard } from "@/features/projects/KanbanBoard";
import { TaskModal } from "@/features/projects/TaskModal";
import { useBoard, useBoardMutation } from "@/features/projects/queries";

export default function ProjectBoardPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = Number(params.projectId);
  const { data: board, isLoading, isError } = useBoard(projectId);
  const [openTaskId, setOpenTaskId] = useState<number | null>(null);

  const archive = useBoardMutation((archived: boolean) =>
    pj.updateProject(projectId, { archived }),
  );

  if (isLoading) return <LoadingRow label="Loading board…" />;
  if (isError || !board)
    return <p className="py-10 text-sm text-rose-400">Project not found.</p>;

  return (
    <div>
      <PageHeader
        title={
          <span className="flex items-center gap-2">
            <Link
              to="/projects"
              className="grid h-7 w-7 place-items-center rounded-lg text-faint transition hover:bg-line/[0.06] hover:text-content"
            >
              <Icon name="chevronLeft" size={18} />
            </Link>
            {board.name}
          </span>
        }
        actions={
          <Button
            variant="secondary"
            icon="inbox"
            onClick={() => archive.mutate(!board.archived)}
          >
            {board.archived ? "Unarchive" : "Archive"}
          </Button>
        }
      />

      <KanbanBoard board={board} onOpenTask={setOpenTaskId} />

      {openTaskId !== null && (
        <TaskModal
          taskId={openTaskId}
          projectId={projectId}
          projectLabels={board.labels}
          onClose={() => setOpenTaskId(null)}
        />
      )}
    </div>
  );
}
