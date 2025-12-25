"use client";

import { useRef, useMemo } from "react";
import { ParticipantTile, useTracks } from "@livekit/components-react";
import { Track } from "livekit-client";
import IconButton from "@/components/ui/IconButton";

type Props = {
    maxVisible?: number;
};

function isHiddenIdentity(identity?: string) {
    if (!identity) return false;
    return identity.includes("_ai-") || identity.startsWith("ai-") || identity.startsWith("AI-");
}

export default function ParticipantStrip({ maxVisible = 6 }: Props) {
    const tracks = useTracks([{ source: Track.Source.Camera, withPlaceholder: true }], {
        onlySubscribed: false,
    });

    const list = useMemo(() => {
        return [...tracks].filter((t) => !isHiddenIdentity(t.participant?.identity));
    }, [tracks]);

    const ref = useRef<HTMLDivElement | null>(null);
    const step = 140 * Math.max(1, Math.floor(maxVisible / 2));

    const shouldCenter = list.length > 0 && list.length <= maxVisible;
    const shouldScroll = list.length > maxVisible;

    return (
        <div className="w-full">
            <div className="flex items-center gap-2">
                {shouldScroll ? (
                    <IconButton size="sm" title="Trước" onClick={() => ref.current?.scrollBy({ left: -step, behavior: "smooth" })}>
                        ‹
                    </IconButton>
                ) : (
                    <div className="w-10" />
                )}

                <div
                    ref={ref}
                    className={[
                        "flex-1 min-w-0",
                        shouldScroll ? "overflow-x-auto scroll-smooth" : "overflow-x-hidden",
                    ].join(" ")}
                >
                    <div
                        className={[
                            "flex gap-2 pr-2",
                            shouldScroll ? "w-max justify-start" : "w-full justify-center", // ✅ đây là phần fix
                        ].join(" ")}
                    >
                        {list.length === 0 ? (
                            <div className="text-xs text-zinc-500 py-2 px-1">Chưa có người tham gia.</div>
                        ) : (
                            list.map((t, idx) => {
                                const key = `${t.participant?.sid ?? t.participant?.identity ?? idx}-${t.source}`;
                                return (
                                    <div
                                        key={key}
                                        className="h-14 w-24 sm:h-16 sm:w-28 shrink-0 overflow-hidden rounded-xl border border-white/10 bg-black"
                                    >
                                        <ParticipantTile trackRef={t} />
                                    </div>
                                );
                            })
                        )}
                    </div>
                </div>

                {shouldScroll ? (
                    <IconButton size="sm" title="Sau" onClick={() => ref.current?.scrollBy({ left: step, behavior: "smooth" })}>
                        ›
                    </IconButton>
                ) : (
                    <div className="w-10" />
                )}
            </div>
        </div>
    );
}
