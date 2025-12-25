"use client";

import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

type IconButtonProps = PropsWithChildren<
  ButtonHTMLAttributes<HTMLButtonElement> & {
    size?: "sm" | "md";
    variant?: "ghost" | "solid";
  }
>;

export default function IconButton({
  size = "md",
  variant = "ghost",
  className = "",
  children,
  ...rest
}: IconButtonProps) {
  const sizeCls = size === "sm" ? "h-8 w-8 text-sm" : "h-10 w-10 text-sm";
  const variantCls =
    variant === "solid"
      ? "bg-white/10 hover:bg-white/15 border border-white/10"
      : "bg-transparent hover:bg-white/10 border border-white/10";

  return (
    <button
      type="button"
      className={`inline-flex items-center justify-center rounded-full transition disabled:cursor-not-allowed disabled:opacity-40 ${sizeCls} ${variantCls} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}
