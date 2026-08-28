export type ToastLevel = "info" | "success" | "error";

export interface Toast {
  id: number;
  message: string;
  level: ToastLevel;
}

let toasts: Toast[] = [];
let nextId = 1;
const listeners = new Set<() => void>();

function emit(): void {
  for (const listener of listeners) listener();
}

export function pushToast(input: { message: string; level?: ToastLevel }): void {
  const toast: Toast = { id: nextId++, message: input.message, level: input.level ?? "info" };
  toasts = [...toasts, toast];
  emit();
  window.setTimeout(() => dismissToast(toast.id), 6000);
}

export function dismissToast(id: number): void {
  toasts = toasts.filter((toast) => toast.id !== id);
  emit();
}

export function subscribeToasts(callback: () => void): () => void {
  listeners.add(callback);
  return () => listeners.delete(callback);
}

export function getToasts(): Toast[] {
  return toasts;
}
