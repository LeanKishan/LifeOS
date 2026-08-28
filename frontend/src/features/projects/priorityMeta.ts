import type { TaskPriority } from "@/features/projects/api";

export const PRIORITY_ORDER: TaskPriority[] = ["low", "medium", "high", "urgent"];

export const PRIORITY_META: Record<TaskPriority, { label: string; pill: string }> = {
  low: {
    label: "Low",
    pill: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400",
  },
  medium: {
    label: "Medium",
    pill: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
  },
  high: {
    label: "High",
    pill: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  },
  urgent: {
    label: "Urgent",
    pill: "bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300",
  },
};
