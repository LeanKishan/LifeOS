import { useState } from "react";
import { Link, useParams } from "react-router-dom";

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

  if (isLoading) return <p className="text-sm text-slate-500">Loading board…</p>;
  if (isError || !board) return <p className="text-sm text-rose-600">Project not found.</p>;

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link to="/projects" className="text-xs text-slate-400 hover:underline">
            ← Projects
          </Link>
          <h2 className="text-xl font-semibold">{board.name}</h2>
        </div>
        <button
          type="button"
          onClick={() => archive.mutate(!board.archived)}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
        >
          {board.archived ? "Unarchive" : "Archive"}
        </button>
      </div>

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
