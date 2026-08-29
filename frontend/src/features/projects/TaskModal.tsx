import { useEffect, useState } from "react";

import { Modal } from "@/components/Modal";
import * as pj from "@/features/projects/api";
import type { Label } from "@/features/projects/api";
import { PRIORITY_META, PRIORITY_ORDER } from "@/features/projects/priorityMeta";
import { useBoardMutation, useTaskDetail } from "@/features/projects/queries";

export function TaskModal({
  taskId,
  projectId,
  projectLabels,
  onClose,
}: {
  taskId: number;
  projectId: number;
  projectLabels: Label[];
  onClose: () => void;
}) {
  const { data: task, isLoading } = useTaskDetail(taskId);

  const patch = useBoardMutation((input: Parameters<typeof pj.updateTask>[1]) =>
    pj.updateTask(taskId, input),
  );
  const setLabels = useBoardMutation((labelIds: number[]) => pj.setTaskLabels(taskId, labelIds));
  const addSub = useBoardMutation((title: string) => pj.addSubtask(taskId, title));
  const patchSub = useBoardMutation((args: { id: number; done: boolean }) =>
    pj.updateSubtask(args.id, { done: args.done }),
  );
  const delSub = useBoardMutation((id: number) => pj.deleteSubtask(id));
  const addComment = useBoardMutation((body: string) => pj.addComment(taskId, body));
  const delComment = useBoardMutation((id: number) => pj.deleteComment(id));
  const addLabel = useBoardMutation((name: string) => pj.addLabel(projectId, { name }));
  const removeTask = useBoardMutation(() => pj.deleteTask(taskId));

  const [description, setDescription] = useState("");
  const [subtaskTitle, setSubtaskTitle] = useState("");
  const [commentBody, setCommentBody] = useState("");
  const [labelName, setLabelName] = useState("");

  useEffect(() => {
    if (task) setDescription(task.description ?? "");
  }, [task]);

  function toggleLabel(labelId: number): void {
    if (!task) return;
    const current = task.labels.map((label) => label.id);
    const next = current.includes(labelId)
      ? current.filter((id) => id !== labelId)
      : [...current, labelId];
    setLabels.mutate(next);
  }

  return (
    <Modal title={task ? task.title : "Task"} onClose={onClose}>
      {isLoading || !task ? (
        <p className="text-sm text-muted">Loading…</p>
      ) : (
        <div className="space-y-5 text-sm">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={task.done}
              onChange={(event) => patch.mutate({ done: event.target.checked })}
              aria-label="Mark done"
            />
            <input
              defaultValue={task.title}
              onBlur={(event) => {
                const value = event.target.value.trim();
                if (value && value !== task.title) patch.mutate({ title: value });
              }}
              className={`w-full rounded-md border border-line/[0.14] px-3 py-2 font-medium outline-none focus:border-brand/60   ${
                task.done ? "text-faint line-through" : ""
              }`}
            />
          </div>

          <div className="flex gap-3">
            <label className="flex-1">
              <span className="mb-1 block text-xs text-muted">Priority</span>
              <select
                value={task.priority}
                onChange={(event) =>
                  patch.mutate({ priority: event.target.value as pj.TaskPriority })
                }
                className="w-full rounded-md border border-line/[0.14] px-2 py-1.5 outline-none focus:border-brand/60 focus:ring-4 focus:ring-brand/15"
              >
                {PRIORITY_ORDER.map((value) => (
                  <option key={value} value={value}>
                    {PRIORITY_META[value].label}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex-1">
              <span className="mb-1 block text-xs text-muted">Due</span>
              <input
                type="date"
                defaultValue={task.due_on ?? ""}
                onChange={(event) => patch.mutate({ due_on: event.target.value || null })}
                className="w-full rounded-md border border-line/[0.14] px-2 py-1.5 outline-none focus:border-brand/60 focus:ring-4 focus:ring-brand/15"
              />
            </label>
          </div>

          <div>
            <span className="mb-1 block text-xs text-muted">Description</span>
            <textarea
              rows={3}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              className="w-full rounded-md border border-line/[0.14] px-3 py-2 outline-none focus:border-brand/60 focus:ring-4 focus:ring-brand/15"
            />
            {description !== (task.description ?? "") && (
              <button
                type="button"
                onClick={() => patch.mutate({ description: description || null })}
                className="mt-1 rounded-md btn-primary btn-sm"
              >
                Save description
              </button>
            )}
          </div>

          <div>
            <span className="mb-1 block text-xs text-muted">Labels</span>
            <div className="flex flex-wrap gap-1.5">
              {projectLabels.map((label) => {
                const active = task.labels.some((assigned) => assigned.id === label.id);
                return (
                  <button
                    key={label.id}
                    type="button"
                    onClick={() => toggleLabel(label.id)}
                    className={`rounded px-2 py-0.5 text-xs font-medium ${
                      active ? "text-white" : "text-muted opacity-60"
                    }`}
                    style={{ backgroundColor: active ? label.color : "transparent", border: `1px solid ${label.color}` }}
                  >
                    {label.name}
                  </button>
                );
              })}
              <form
                onSubmit={(event) => {
                  event.preventDefault();
                  const value = labelName.trim();
                  if (value) addLabel.mutate(value, { onSuccess: () => setLabelName("") });
                }}
              >
                <input
                  value={labelName}
                  onChange={(event) => setLabelName(event.target.value)}
                  placeholder="+ label"
                  className="w-20 rounded border border-line/[0.14] px-1.5 py-0.5 text-xs outline-none focus:border-brand/60 focus:ring-4 focus:ring-brand/15"
                />
              </form>
            </div>
          </div>

          <div>
            <span className="mb-1 block text-xs text-muted">
              Subtasks {task.subtask_done}/{task.subtask_total}
            </span>
            <ul className="space-y-1">
              {task.subtasks.map((subtask) => (
                <li key={subtask.id} className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={subtask.done}
                    onChange={(event) =>
                      patchSub.mutate({ id: subtask.id, done: event.target.checked })
                    }
                  />
                  <span className={subtask.done ? "text-faint line-through" : ""}>
                    {subtask.title}
                  </span>
                  <button
                    type="button"
                    onClick={() => delSub.mutate(subtask.id)}
                    className="ml-auto text-faint hover:text-rose-500"
                    aria-label="Delete subtask"
                  >
                    ✕
                  </button>
                </li>
              ))}
            </ul>
            <form
              className="mt-1"
              onSubmit={(event) => {
                event.preventDefault();
                const value = subtaskTitle.trim();
                if (value) addSub.mutate(value, { onSuccess: () => setSubtaskTitle("") });
              }}
            >
              <input
                value={subtaskTitle}
                onChange={(event) => setSubtaskTitle(event.target.value)}
                placeholder="+ Add subtask"
                className="w-full rounded-md border border-line/[0.14] px-2 py-1 text-sm outline-none focus:border-brand/60 focus:ring-4 focus:ring-brand/15"
              />
            </form>
          </div>

          <div>
            <span className="mb-1 block text-xs text-muted">Comments</span>
            <ul className="space-y-1.5">
              {task.comments.map((comment) => (
                <li
                  key={comment.id}
                  className="flex items-start gap-2 rounded-md bg-surface-2 px-2 py-1 "
                >
                  <span className="flex-1">{comment.body}</span>
                  <button
                    type="button"
                    onClick={() => delComment.mutate(comment.id)}
                    className="text-faint hover:text-rose-500"
                    aria-label="Delete comment"
                  >
                    ✕
                  </button>
                </li>
              ))}
            </ul>
            <form
              className="mt-1 flex gap-2"
              onSubmit={(event) => {
                event.preventDefault();
                const value = commentBody.trim();
                if (value) addComment.mutate(value, { onSuccess: () => setCommentBody("") });
              }}
            >
              <input
                value={commentBody}
                onChange={(event) => setCommentBody(event.target.value)}
                placeholder="Add a comment…"
                className="flex-1 rounded-md border border-line/[0.14] px-2 py-1 text-sm outline-none focus:border-brand/60 focus:ring-4 focus:ring-brand/15"
              />
              <button
                type="submit"
                className="rounded-md btn-primary btn-md"
              >
                Post
              </button>
            </form>
          </div>

          <button
            type="button"
            onClick={() => removeTask.mutate(undefined, { onSuccess: onClose })}
            className="text-xs font-medium text-rose-600 hover:underline"
          >
            Delete task
          </button>
        </div>
      )}
    </Modal>
  );
}
