
import type { ReactNode } from "react";

type PageHeaderProps = {
    title: string;
    subtitle?: string;
    className?: string;
    color?: string;
    bleed?: boolean;
    bleedClass?: string;
    collapseTop?: boolean;
    actions?: ReactNode;
};

const DEFAULT_COLOR = "#1F2A7A";

export default function PageHeader({
    title,
    subtitle,
    className = "",
    color = DEFAULT_COLOR,
    bleed = true,
    bleedClass = "-mx-8",
    collapseTop = false,
    actions,
}: PageHeaderProps) {
    const bleedX = bleed ? bleedClass : "";
    const flushTop = collapseTop ? "-mt-8" : "";

    return (
        <section
            className={`${bleedX} ${flushTop} mb-6 rounded-xl px-6 py-8 shadow-sm ${className}`}
            style={{ backgroundColor: color }}
        >
            <div className="flex items-start justify-between gap-4">
                <div>
                    <h1 className="text-2xl md:text-3xl font-bold text-white">{title}</h1>
                    {subtitle ? (
                        <p className="mt-1 text-sm font-medium text-white/90">{subtitle}</p>
                    ) : null}
                </div>

                {actions ? <div className="shrink-0">{actions}</div> : null}
            </div>
        </section>
    );
}
