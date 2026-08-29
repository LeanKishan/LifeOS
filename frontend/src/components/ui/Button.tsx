import type { ButtonHTMLAttributes, ReactNode } from "react";
import { Link } from "react-router-dom";

import { Icon, type IconName } from "@/components/icons";
import { cn } from "@/lib/cn";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";

const VARIANT: Record<Variant, string> = {
  primary: "btn-primary",
  secondary: "btn-secondary",
  ghost: "btn-ghost",
  danger: "btn-danger",
};
const SIZE: Record<Size, string> = { sm: "btn-sm", md: "btn-md", lg: "btn-lg" };

interface CommonProps {
  variant?: Variant;
  size?: Size;
  icon?: IconName;
  iconRight?: IconName;
  loading?: boolean;
  block?: boolean;
  children?: ReactNode;
  className?: string;
}

type ButtonProps = CommonProps &
  Omit<ButtonHTMLAttributes<HTMLButtonElement>, "className"> & {
    to?: string;
    href?: string;
  };

export function Button({
  variant = "secondary",
  size = "md",
  icon,
  iconRight,
  loading,
  block,
  children,
  className,
  to,
  href,
  disabled,
  ...rest
}: ButtonProps) {
  const cls = cn(VARIANT[variant], SIZE[size], block && "w-full", className);
  const inner = (
    <>
      {loading ? (
        <Icon name="refresh" size={size === "sm" ? 14 : 16} className="spin" />
      ) : (
        icon && <Icon name={icon} size={size === "sm" ? 14 : 16} />
      )}
      {children}
      {iconRight && !loading && <Icon name={iconRight} size={size === "sm" ? 14 : 16} />}
    </>
  );

  if (to) {
    return (
      <Link to={to} className={cls}>
        {inner}
      </Link>
    );
  }
  if (href) {
    return (
      <a href={href} target="_blank" rel="noreferrer" className={cls}>
        {inner}
      </a>
    );
  }
  return (
    <button className={cls} disabled={disabled || loading} {...rest}>
      {inner}
    </button>
  );
}

export function IconButton({
  name,
  label,
  size = 36,
  className,
  ...rest
}: { name: IconName; label: string; size?: number } & ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className={cn(
        "inline-flex items-center justify-center rounded-xl border border-line/[0.1] bg-surface-2 text-muted",
        "transition hover:border-brand/40 hover:text-content active:scale-95",
        className,
      )}
      style={{ width: size, height: size }}
      {...rest}
    >
      <Icon name={name} size={Math.round(size * 0.5)} />
    </button>
  );
}
