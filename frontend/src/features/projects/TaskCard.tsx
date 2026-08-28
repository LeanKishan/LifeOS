import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

import type { TaskCard as TaskCardData } from "@/features/projects/api";
import { PRIORITY_META } from "@/features/projects/priorityMeta";

export function TaskCard({
  task,
  onOpen,
}: {
  task: TaskCardData;
  onOpen: (taskId: number) => void;
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: task.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="rounded-lg border border-slate-200 bg-white p-2.5 text-sm shadow-sm dark:border-slate-800 dark:bg-slate-900"
    >
      <div className="flex items-start gap-2">
        <button
          type="button"
          {...attributes}
          {...listeners}
          aria-label="Drag task"
          className="mt-0.5 cursor-grab select-none px-0.5 text-slate-300 hover:text-slate-500 active:cursor-grabbing"
        >
          ⠿
        </button>
        <button
          type="button"
          onClick={() => onOpen(task.id)}
          className="min-w-0 flex-1 text-left"
        >
          <div className={`font-medium ${task.done ? "text-slate-400 line-through" : ""}`}>
            {task.title}
          </div>
          <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
            <span
              className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${PRIORITY_META[task.priority].pill}`}
            >
              {PRIORITY_META[task.priority].label}
            </span>
            {task.labels.map((label) => (
              <span
                key={label.id}
                className="rounded px-1.5 py-0.5 text-[10px] font-medium text-white"
                style={{ backgroundColor: label.color }}
              >
                {label.name}
              </span>
            ))}
            {task.subtask_total > 0 && (
              <span className="text-[11px] text-slate-400">
                ☑ {task.subtask_done}/{task.subtask_total}
              </span>
            )}
            {task.comment_count > 0 && (
              <span className="text-[11px] text-slate-400">💬 {task.comment_count}</span>
            )}
            {task.due_on && <span className="text-[11px] text-slate-400">📅 {task.due_on}</span>}
          </div>
        </button>
      </div>
    </div>
  );
}
