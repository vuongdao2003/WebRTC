"use client";

import * as React from "react";

function cn(...cls: Array<string | false | null | undefined>) {
  return cls.filter(Boolean).join(" ");
}

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

const Input = React.forwardRef<HTMLInputElement, InputProps>(function Input(
  { className, ...props },
  ref
) {
  return (
    <input
      ref={ref}
      {...props}
      className={cn(

        "w-full rounded-lg border border-gray-300 bg-white px-4 py-2",

        "text-gray-900 placeholder-gray-400 caret-gray-900",

        "focus:outline-none focus:ring-2 focus:ring-[#2F327D] focus:border-[#2F327D]",

        "disabled:opacity-60 disabled:cursor-not-allowed",
        className
      )}
    />
  );
});

export default Input;
