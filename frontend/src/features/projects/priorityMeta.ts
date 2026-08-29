import type { TaskPriority } from "@/features/projects/api";

export const PRIORITY_ORDER: TaskPriority[] = ["low", "medium", "high", "urgent"];

export const PRIORITY_META: Record<TaskPriority, { label: string; pill: string }> = {
  low: {
    label: "Low",
    pill: "pill bg-line/[0.06] text-faint ring-line/10",
  },
  medium: {
    label: "Medium",
    pill: "pill bg-blue-500/12 text-blue-300 ring-blue-500/20",
  },
  high: {
    label: "High",
    pill: "pill bg-amber-500/12 text-amber-300 ring-amber-500/20",
  },
  urgent: {
    label: "Urgent",
    pill: "pill bg-rose-500/12 text-rose-300 ring-rose-500/20",
  },
};
