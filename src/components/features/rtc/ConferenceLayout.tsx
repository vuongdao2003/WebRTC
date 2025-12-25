"use client";

import type { TrackReferenceOrPlaceholder } from "@livekit/components-react";
import { ControlBar, ParticipantTile, useTracks } from "@livekit/components-react";
import { Track } from "livekit-client";
import ParticipantStrip from "@/components/features/rtc/ParticipantStrip";

type Props = {
    roomId: string;
    displayName: string;
};

const MAX_PER_ROW = 3;
const MAX_TILES = 12;

type ExtraTile = { __extra: true; count: number };
type TileItem = TrackReferenceOrPlaceholder | ExtraTile;

function isExtraTile(item: TileItem): item is ExtraTile {
    return (item as any).__extra === true;
}

function isHiddenIdentity(identity?: string) {
    if (!identity) return false;
    return identity.includes("_ai-") || identity.startsWith("ai-") || identity.startsWith("AI-");
}

export default function ConferenceLayout({ roomId, displayName }: Props) {
    const tracks = useTracks(
        [
            { source: Track.Source.ScreenShare, withPlaceholder: false },
            { source: Track.Source.Camera, withPlaceholder: true },
        ],
        { onlySubscribed: false }
    );

    // ✅ Lọc participant AI để không tạo placeholder/ô đen khi mở tab "Bảng lỗi"
    const all: TrackReferenceOrPlaceholder[] = [...tracks].filter(
        (t) => !isHiddenIdentity(t.participant?.identity)
    );

    let visible: TrackReferenceOrPlaceholder[] = all;
    let extraCount = 0;

    if (all.length > MAX_TILES) {
        visible = all.slice(0, MAX_TILES - 1);
        extraCount = all.length - (MAX_TILES - 1);
    }

    const items: TileItem[] = [...visible];
    if (extraCount > 0) items.push({ __extra: true, count: extraCount });

    const rows: TileItem[][] = [];
    for (let i = 0; i < items.length; i += MAX_PER_ROW) {
        rows.push(items.slice(i, i + MAX_PER_ROW));
    }

    const hasMultipleRows = rows.length > 1;
    const singleRowCount = rows[0]?.length ?? 0;

    return (
        <div className="flex h-full flex-col bg-black text-white overflow-hidden">
            {/* (C) Danh sách người tham gia */}
            <div className="shrink-0 border-b border-zinc-800 bg-zinc-950 px-3 py-2">
                <ParticipantStrip maxVisible={6} />
            </div>

            {/* (B) Khu video */}
            <main className="flex-1 min-h-0 px-3 py-3">
                <div className="h-full w-full overflow-y-auto rounded-xl bg-zinc-900 p-3">
                    {rows.length === 0 ? (
                        <div className="flex h-full items-center justify-center text-sm text-zinc-400">
                            Chưa có người tham gia nào trong phòng.
                        </div>
                    ) : (
                        <div className="flex h-full flex-col justify-center gap-4">
                            {rows.map((row, rowIndex) => (
                                <div key={rowIndex} className="flex justify-center gap-4">
                                    {row.map((item, idx) => {
                                        let sizeClass = "";

                                        if (!hasMultipleRows) {
                                            if (singleRowCount === 1) sizeClass = "w-full max-w-[960px]";
                                            else if (singleRowCount === 2) sizeClass = "w-1/2 max-w-[720px]";
                                            else sizeClass = "w-1/3 max-w-[640px]";
                                        } else {
                                            sizeClass = "flex-1 max-w-[420px]";
                                        }

                                        if (isExtraTile(item)) {
                                            return (
                                                <div
                                                    key={`extra-${rowIndex}-${idx}`}
                                                    className={`${sizeClass} aspect-video overflow-hidden rounded-xl border border-zinc-700 bg-black flex items-center justify-center`}
                                                >
                                                    <span className="text-2xl font-semibold text-zinc-200">+{item.count}</span>
                                                </div>
                                            );
                                        }

                                        const trackRef = item;
                                        const key = `${trackRef.participant?.sid ?? trackRef.participant?.identity ?? idx}-${trackRef.source}`;

                                        return (
                                            <div
                                                key={key}
                                                className={`${sizeClass} aspect-video overflow-hidden rounded-xl border border-zinc-700 bg-black tileStage`}
                                            >
                                                <ParticipantTile trackRef={trackRef} />
                                            </div>
                                        );
                                    })}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </main>

            {/* (D) Thanh nút + nút Bảng lỗi */}
            <footer className="shrink-0 border-t border-zinc-800 bg-zinc-900/90 px-3 py-2">
                <div className="flex items-center justify-between">
                    <div className="flex-1 flex justify-center">
                        <ControlBar variation="minimal" />
                    </div>

                    <button
                        type="button"
                        onClick={() => {
                            const url = `/ai?room=${encodeURIComponent(roomId)}&name=${encodeURIComponent(displayName)}`;
                            window.open(url, "_blank", "noopener,noreferrer");
                        }}
                        className="ml-3 rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-xs font-semibold text-zinc-100 hover:bg-zinc-700"
                        title="Mở bảng lỗi trong tab mới"
                    >
                        Bảng lỗi
                    </button>
                </div>
            </footer>
        </div>
    );
}
