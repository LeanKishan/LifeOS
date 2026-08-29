import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

import { Icon } from "@/components/icons";
import type { TaskCard as TaskCardData } from "@/features/projects/api";
import { PRIORITY_META } from "@/features/projects/priorityMeta";
import { cn } from "@/lib/cn";

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
      className={cn(
        "rounded-xl border border-line/[0.08] bg-elev p-3 text-sm shadow-card transition",
        !isDragging && "hover:border-line/20",
      )}
    >
      <div className="flex items-start gap-2">
        <button
          type="button"
          {...attributes}
          {...listeners}
          aria-label="Drag task"
          className="mt-0.5 cursor-grab text-faint transition hover:text-muted active:cursor-grabbing"
        >
          <Icon name="dots" size={14} />
        </button>
        <button type="button" onClick={() => onOpen(task.id)} className="min-w-0 flex-1 text-left">
          <div className={cn("font-medium text-content", task.done && "text-faint line-through")}>
            {task.title}
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            <span className={cn("!px-1.5 !py-0.5 text-[10px]", PRIORITY_META[task.priority].pill)}>
              {PRIORITY_META[task.priority].label}
            </span>
            {task.labels.map((label) => (
              <span
                key={label.id}
                className="rounded-full px-1.5 py-0.5 text-[10px] font-medium text-white"
                style={{ backgroundColor: label.color }}
              >
                {label.name}
              </span>
            ))}
            {task.subtask_total > 0 && (
              <span className="flex items-center gap-1 text-[11px] text-faint">
                <Icon name="check" size={11} />
                {task.subtask_done}/{task.subtask_total}
              </span>
            )}
            {task.comment_count > 0 && (
              <span className="flex items-center gap-1 text-[11px] text-faint">
                <Icon name="sparkles" size={11} />
                {task.comment_count}
              </span>
            )}
            {task.due_on && (
              <span className="flex items-center gap-1 text-[11px] text-faint">
                <Icon name="calendar" size={11} />
                {task.due_on}
              </span>
            )}
          </div>
        </button>
      </div>
    </div>
  );
}
