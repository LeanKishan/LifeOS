import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as pj from "@/features/projects/api";
import type { Board } from "@/features/projects/api";

const listKey = ["projects", "list"] as const;
const boardKey = (projectId: number) => ["projects", "board", projectId] as const;
const taskKey = (taskId: number) => ["projects", "task", taskId] as const;

export function useProjects(archived = false) {
  return useQuery({
    queryKey: [...listKey, archived],
    queryFn: () => pj.listProjects(archived),
  });
}

export function useBoard(projectId: number) {
  return useQuery({ queryKey: boardKey(projectId), queryFn: () => pj.getBoard(projectId) });
}

export function useTaskDetail(taskId: number | null) {
  return useQuery({
    queryKey: taskKey(taskId ?? 0),
    queryFn: () => pj.getTask(taskId as number),
    enabled: taskId !== null,
  });
}

export function useCreateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: pj.createProject,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });
}

/** Mirror of the backend move: pull the task out, re-insert, renumber. */
export function applyTaskMove(
  board: Board,
  taskId: number,
  columnId: number,
  position: number,
): Board {
  let moved: Board["columns"][number]["tasks"][number] | undefined;
  const withoutTask = board.columns.map((column) => {
    const index = column.tasks.findIndex((task) => task.id === taskId);
    if (index === -1) return column;
    moved = column.tasks[index];
    return { ...column, tasks: column.tasks.filter((task) => task.id !== taskId) };
  });
  if (!moved) return board;
  const movedTask = { ...moved, column_id: columnId };

  return {
    ...board,
    columns: withoutTask.map((column) => {
      if (column.id !== columnId) {
        return { ...column, tasks: column.tasks.map((task, i) => ({ ...task, position: i })) };
      }
      const tasks = [...column.tasks];
      tasks.splice(Math.max(0, Math.min(position, tasks.length)), 0, movedTask);
      return { ...column, tasks: tasks.map((task, i) => ({ ...task, position: i })) };
    }),
  };
}

export function useMoveTask(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (args: { taskId: number; columnId: number; position: number }) =>
      pj.moveTask(args.taskId, args.columnId, args.position),
    onMutate: async ({ taskId, columnId, position }) => {
      await qc.cancelQueries({ queryKey: boardKey(projectId) });
      const previous = qc.getQueryData<Board>(boardKey(projectId));
      if (previous) {
        qc.setQueryData<Board>(
          boardKey(projectId),
          applyTaskMove(previous, taskId, columnId, position),
        );
      }
      return { previous };
    },
    onError: (_error, _args, context) => {
      if (context?.previous) qc.setQueryData(boardKey(projectId), context.previous);
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });
}

/** Any board/task mutation that doesn't need optimism — just refetch. */
export function useBoardMutation<TArgs>(fn: (args: TArgs) => Promise<unknown>) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: fn,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });
}
