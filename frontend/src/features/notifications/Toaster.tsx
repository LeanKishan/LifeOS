import { useSyncExternalStore } from "react";

import { dismissToast, getToasts, subscribeToasts, type ToastLevel } from "./toasts";

const LEVEL_CLASS: Record<ToastLevel, string> = {
  info: "border-slate-300 dark:border-slate-600",
  success: "border-emerald-400",
  error: "border-rose-400",
};

export function Toaster() {
  const toasts = useSyncExternalStore(subscribeToasts, getToasts, getToasts);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex w-72 flex-col gap-2">
      {toasts.map((toast) => (
        <button
          key={toast.id}
          type="button"
          onClick={() => dismissToast(toast.id)}
          className={`rounded-lg border bg-white px-3 py-2 text-left text-sm shadow-lg dark:bg-slate-900 ${LEVEL_CLASS[toast.level]}`}
        >
          {toast.message}
        </button>
      ))}
    </div>
  );
}
