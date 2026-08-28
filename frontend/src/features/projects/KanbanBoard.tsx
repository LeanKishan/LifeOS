import { useState } from "react";
import {
  DndContext,
  PointerSensor,
  closestCorners,
  useDroppable,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";

import * as pj from "@/features/projects/api";
import type { Board, BoardColumn } from "@/features/projects/api";
import { TaskCard } from "@/features/projects/TaskCard";
import { useBoardMutation, useMoveTask } from "@/features/projects/queries";

function AddTaskInline({ projectId, columnId }: { projectId: number; columnId: number }) {
  const [title, setTitle] = useState("");
  const create = useBoardMutation((newTitle: string) =>
    pj.createTask(projectId, { column_id: columnId, title: newTitle }),
  );

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        const value = title.trim();
        if (value) create.mutate(value, { onSuccess: () => setTitle("") });
      }}
    >
      <input
        value={title}
        onChange={(event) => setTitle(event.target.value)}
        placeholder="+ Add task"
        className="w-full rounded-md border border-transparent bg-transparent px-2 py-1 text-sm outline-none placeholder:text-slate-400 hover:border-slate-300 focus:border-emerald-500 dark:hover:border-slate-700"
      />
    </form>
  );
}

function Column({
  column,
  index,
  total,
  onOpenTask,
}: {
  column: BoardColumn;
  index: number;
  total: number;
  onOpenTask: (taskId: number) => void;
}) {
  const { setNodeRef } = useDroppable({ id: `col-${column.id}` });
  const moveCol = useBoardMutation((position: number) => pj.moveColumn(column.id, position));
  const removeCol = useBoardMutation(() => pj.deleteColumn(column.id));

  return (
    <div className="w-72 shrink-0">
      <div className="mb-2 flex items-center gap-2 px-1 text-sm font-medium">
        <span>{column.name}</span>
        <span className="text-slate-400">{column.tasks.length}</span>
        <span className="ml-auto flex items-center gap-1 text-slate-300">
          <button
            type="button"
            disabled={index === 0}
            onClick={() => moveCol.mutate(index - 1)}
            className="hover:text-slate-600 disabled:opacity-30"
            aria-label="Move column left"
          >
            ◀
          </button>
          <button
            type="button"
            disabled={index === total - 1}
            onClick={() => moveCol.mutate(index + 1)}
            className="hover:text-slate-600 disabled:opacity-30"
            aria-label="Move column right"
          >
            ▶
          </button>
          <button
            type="button"
            onClick={() => removeCol.mutate(undefined)}
            className="hover:text-rose-500"
            aria-label="Delete column"
          >
            ✕
          </button>
        </span>
      </div>
      <SortableContext
        items={column.tasks.map((task) => task.id)}
        strategy={verticalListSortingStrategy}
      >
        <div
          ref={setNodeRef}
          className="min-h-16 space-y-2 rounded-lg bg-slate-100/70 p-2 dark:bg-slate-900/40"
        >
          {column.tasks.map((task) => (
            <TaskCard key={task.id} task={task} onOpen={onOpenTask} />
          ))}
          <AddTaskInline projectId={column.project_id} columnId={column.id} />
        </div>
      </SortableContext>
    </div>
  );
}

function AddColumn({ projectId }: { projectId: number }) {
  const [name, setName] = useState("");
  const [open, setOpen] = useState(false);
  const create = useBoardMutation((newName: string) => pj.addColumn(projectId, newName));

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="h-9 shrink-0 rounded-lg border border-dashed border-slate-300 px-3 text-sm text-slate-500 hover:border-slate-400 dark:border-slate-700"
      >
        + Column
      </button>
    );
  }

  return (
    <form
      className="shrink-0"
      onSubmit={(event) => {
        event.preventDefault();
        const value = name.trim();
        if (value)
          create.mutate(value, {
            onSuccess: () => {
              setName("");
              setOpen(false);
            },
          });
      }}
    >
      <input
        autoFocus
        value={name}
        onBlur={() => !name && setOpen(false)}
        onChange={(event) => setName(event.target.value)}
        placeholder="Column name"
        className="w-40 rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm outline-none focus:border-emerald-500 dark:border-slate-700 dark:bg-slate-900"
      />
    </form>
  );
}

export function KanbanBoard({
  board,
  onOpenTask,
}: {
  board: Board;
  onOpenTask: (taskId: number) => void;
}) {
  const move = useMoveTask(board.id);
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

  function locate(taskId: number): { columnId: number; index: number } | null {
    for (const column of board.columns) {
      const index = column.tasks.findIndex((task) => task.id === taskId);
      if (index !== -1) return { columnId: column.id, index };
    }
    return null;
  }

  function onDragEnd(event: DragEndEvent): void {
    const { active, over } = event;
    if (!over) return;

    const taskId = Number(active.id);
    const from = locate(taskId);
    if (!from) return;

    const overId = String(over.id);
    let columnId: number;
    let position: number;

    if (overId.startsWith("col-")) {
      columnId = Number(overId.slice(4));
      const column = board.columns.find((c) => c.id === columnId);
      position = column ? column.tasks.length : 0;
    } else {
      const overLocation = locate(Number(over.id));
      if (!overLocation) return;
      columnId = overLocation.columnId;
      position = overLocation.index;
    }

    if (from.columnId === columnId && from.index === position) return;
    move.mutate({ taskId, columnId, position });
  }

  return (
    <DndContext sensors={sensors} collisionDetection={closestCorners} onDragEnd={onDragEnd}>
      <div className="flex gap-4 overflow-x-auto pb-4">
        {board.columns.map((column, index) => (
          <Column
            key={column.id}
            column={column}
            index={index}
            total={board.columns.length}
            onOpenTask={onOpenTask}
          />
        ))}
        <AddColumn projectId={board.id} />
      </div>
    </DndContext>
  );
}
