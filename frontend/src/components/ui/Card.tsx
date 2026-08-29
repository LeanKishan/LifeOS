import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

export function Card({
  children,
  className,
  glass,
  hover,
  as: As = "div",
}: {
  children: ReactNode;
  className?: string;
  glass?: boolean;
  hover?: boolean;
  as?: "div" | "section" | "article";
}) {
  return (
    <As
      className={cn(
        glass ? "surface-glass" : "surface-card",
        hover && "card-hover",
        "p-5",
        className,
      )}
    >
      {children}
    </As>
  );
}

export function CardHeader({
  title,
  action,
  className,
}: {
  title: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("mb-3 flex items-center justify-between gap-3", className)}>
      <h3 className="text-sm font-semibold text-muted">{title}</h3>
      {action}
    </div>
  );
}
