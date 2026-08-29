import { useSyncExternalStore } from "react";

import { Icon, type IconName } from "@/components/icons";
import { cn } from "@/lib/cn";
import { dismissToast, getToasts, subscribeToasts, type ToastLevel } from "./toasts";

const META: Record<ToastLevel, { icon: IconName; ring: string; fg: string }> = {
  info: { icon: "bell", ring: "ring-line/10", fg: "text-muted" },
  success: { icon: "check", ring: "ring-brand/25", fg: "text-brand-hi" },
  error: { icon: "x", ring: "ring-rose-500/25", fg: "text-rose-300" },
};

export function Toaster() {
  const toasts = useSyncExternalStore(subscribeToasts, getToasts, getToasts);
  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[60] flex w-80 flex-col gap-2">
      {toasts.map((toast) => {
        const m = META[toast.level];
        return (
          <button
            key={toast.id}
            type="button"
            onClick={() => dismissToast(toast.id)}
            className={cn(
              "flex animate-slide-in-right items-start gap-2.5 rounded-xl border border-line/[0.1] bg-elev px-3.5 py-3 text-left text-sm text-content shadow-pop ring-1 backdrop-blur-xl",
              m.ring,
            )}
          >
            <Icon name={m.icon} size={16} className={cn("mt-0.5 shrink-0", m.fg)} />
            <span className="flex-1">{toast.message}</span>
          </button>
        );
      })}
    </div>
  );
}
