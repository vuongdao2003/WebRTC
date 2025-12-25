import type { HTMLAttributes, PropsWithChildren } from "react";

type CardProps = PropsWithChildren<
    HTMLAttributes<HTMLDivElement> & {
        tone?: "light" | "dark";
    }
>;

export default function Card({
    tone = "light",
    className = "",
    children,
    ...rest
}: CardProps) {
    const base =
        "rounded-2xl border shadow-sm " +
        (tone === "dark"
            ? "border-zinc-800 bg-zinc-950/70 text-white"
            : "border-zinc-200 bg-white text-black");

    return (
        <div className={`${base} ${className}`} {...rest}>
            {children}
        </div>
    );
}
