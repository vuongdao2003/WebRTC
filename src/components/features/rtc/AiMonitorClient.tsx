"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import { useTracks } from "@livekit/components-react";
import { Track } from "livekit-client";
import type { LocalVideoTrack, RemoteVideoTrack } from "livekit-client";
import { createDetectionClient, type DetectionResult } from "@/api/detection";

type Props = {
    roomName: string;
    displayName?: string;
};

type AnyVideoTrack = LocalVideoTrack | RemoteVideoTrack;

function isHiddenIdentity(identity?: string) {
    if (!identity) return false;
    // tab AI join room với tên dạng: tung_ai-xxxx
    return identity.includes("_ai-") || identity.startsWith("ai-") || identity.startsWith("AI-");
}

function toVideoTrack(t: unknown): AnyVideoTrack | null {
    const tr = t as any;
    if (!tr) return null;
    if (tr.kind !== Track.Kind.Video) return null;
    if (typeof tr.attach !== "function") return null;
    if (typeof tr.detach !== "function") return null;
    return tr as AnyVideoTrack;
}

type ErrItem = {
    frame_id: number;
    error: string;
    dataUrl: string; // ảnh chụp frame bị lỗi
    at: number; // timestamp
};

export default function AiMonitorClient({ roomName }: Props) {
    // Lấy camera tracks (kể cả placeholder nếu bạn muốn)
    const tracks = useTracks([{ source: Track.Source.Camera, withPlaceholder: true }], {
        onlySubscribed: false,
    });

    // Lọc bỏ participant của tab AI để không tạo “ô đen” bên phòng chính
    const cameraTracks = useMemo(() => {
        return [...tracks].filter((t) => !isHiddenIdentity(t.participant?.identity));
    }, [tracks]);

    // Danh sách participant unique theo sid
    const participants = useMemo(() => {
        const map = new Map<string, { sid: string; name: string }>();
        for (const t of cameraTracks) {
            const sid = t.participant?.sid;
            if (!sid) continue;
            if (!map.has(sid)) {
                map.set(sid, {
                    sid,
                    name: t.participant?.name || t.participant?.identity || sid,
                });
            }
        }
        return Array.from(map.values());
    }, [cameraTracks]);

    const [selectedSid, setSelectedSid] = useState<string | null>(null);

    // auto chọn người đầu tiên
    useEffect(() => {
        if (!selectedSid && participants.length > 0) setSelectedSid(participants[0].sid);
    }, [participants, selectedSid]);

    const selectedTrackRef = useMemo(() => {
        if (!selectedSid) return null;
        return cameraTracks.find((t) => t.participant?.sid === selectedSid) ?? null;
    }, [cameraTracks, selectedSid]);

    // WS state + counters
    const [wsStatus, setWsStatus] = useState<"idle" | "connecting" | "open" | "closed" | "error">("idle");
    const [sendCount, setSendCount] = useState(0);

    // Lưu ảnh lỗi theo sid
    const [errorsBySid, setErrorsBySid] = useState<Record<string, ErrItem[]>>({});

    // giữ frame đã gửi để khi server trả error thì show lại đúng ảnh
    const pendingFramesRef = useRef<Map<number, { sid: string; dataUrl: string; at: number }>>(new Map());
    const frameIdRef = useRef(0);

    // video hidden + canvas capture
    const videoElRef = useRef<HTMLVideoElement | null>(null);
    const canvasRef = useRef<HTMLCanvasElement | null>(null);

    // Detection client
    const detRef = useRef<ReturnType<typeof createDetectionClient> | null>(null);

    // Connect WS 1 lần
    useEffect(() => {
        const det = createDetectionClient({
            debug: true,
            onOpen: () => {
                setWsStatus("open");
                // send handshake to register room/participant on server
                try {
                    const name = (displayName ?? new URLSearchParams(window.location.search).get('name')) ?? '';
                    if (name) {
                        // detRef.current will be set right after creation
                        setTimeout(() => detRef.current?.sendHandshake(roomName, name), 50);
                    }
                } catch (e) {
                    console.warn('[AI] handshake failed', e);
                }
            },
            onClose: () => setWsStatus("closed"),
            onError: () => setWsStatus("error"),
            onMessage: (msg) => handleWsMessage(msg),
        });

        detRef.current = det;
        setWsStatus("connecting");
        det.connect();

        return () => {
            det.close();
            detRef.current = null;
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Attach/detach livekit track vào video hidden khi đổi selectedSid
    useEffect(() => {
        const el = videoElRef.current;
        if (!el) return;

        const raw = selectedTrackRef?.publication?.track;
        const vt = toVideoTrack(raw);

        if (!vt) return;

        vt.attach(el);
        el.muted = true;
        el.playsInline = true;
        el.play().catch(() => { });

        return () => {
            try {
                vt.detach(el);
            } catch { }
        };
    }, [selectedTrackRef]);

    function handleWsMessage(msg: DetectionResult) {
        // server nên trả sid + frame_id + error
        const sid = msg.sid;
        const frame_id = msg.frame_id;
        const error =
            msg.error ??
            (msg.logic?.cheating ? msg.logic.reason || "cheating" : null);

        if (!sid || typeof frame_id !== "number") return;
        if (!error) return; // chỉ hiển thị khi có lỗi

        const pending = pendingFramesRef.current.get(frame_id);
        if (!pending) return;

        // đảm bảo sid khớp
        if (pending.sid !== sid) return;

        setErrorsBySid((prev) => {
            const next = { ...prev };
            const arr = next[sid] ? [...next[sid]] : [];
            arr.unshift({
                frame_id,
                error: String(error),
                dataUrl: pending.dataUrl,
                at: Date.now(),
            });
            next[sid] = arr.slice(0, 200); // giới hạn
            return next;
        });

        // xóa pending để tránh leak
        pendingFramesRef.current.delete(frame_id);
    }

    // Loop gửi frame (fps = 1.0)
    useEffect(() => {
        const fps = 1;
        const intervalMs = Math.max(200, Math.round(1000 / fps));

        const timer = window.setInterval(() => {
            const det = detRef.current;
            if (!det || det.status !== "open") return;
            if (!selectedSid) return;

            const v = videoElRef.current;
            if (!v) return;
            if (!v.videoWidth || !v.videoHeight) return;

            const raw = selectedTrackRef?.publication?.track;
            const vt = toVideoTrack(raw);
            if (!vt) return;

            const c = canvasRef.current ?? document.createElement("canvas");
            canvasRef.current = c;

            c.width = v.videoWidth;
            c.height = v.videoHeight;

            const ctx = c.getContext("2d");
            if (!ctx) return;

            ctx.drawImage(v, 0, 0, c.width, c.height);

            const dataUrl = c.toDataURL("image/jpeg", 0.75);
            const b64 = dataUrl.split(",")[1] ?? "";

            frameIdRef.current += 1;
            const frame_id = frameIdRef.current;

            // lưu pending để khi server báo lỗi thì show lại ảnh này
            pendingFramesRef.current.set(frame_id, {
                sid: selectedSid,
                dataUrl,
                at: Date.now(),
            });

            console.log("[AI] send frame", {
                frame_id,
                sid: selectedSid,
                bytes: b64.length,
                time: new Date().toISOString(),
            });

            det.sendFrame({
                image: b64,
                sid: selectedSid,
                frame_id,
            });

            setSendCount((x) => x + 1);

            // prune pending cũ > 30s
            const now = Date.now();
            for (const [k, val] of pendingFramesRef.current.entries()) {
                if (now - val.at > 30_000) pendingFramesRef.current.delete(k);
            }
        }, intervalMs);

        return () => window.clearInterval(timer);
    }, [selectedSid, selectedTrackRef]);

    const selectedErrors = selectedSid ? errorsBySid[selectedSid] ?? [] : [];

    return (
        <div className="h-full w-full bg-white">
            {/* video hidden để capture */}
            <video ref={videoElRef} className="hidden" />
            <canvas ref={canvasRef} className="hidden" />

            <div className="h-full grid grid-cols-[320px_1fr]">
                {/* LEFT: danh sách participant */}
                <aside className="border-r border-slate-200 bg-white">
                    <div className="px-4 py-4">
                        <div className="text-xl font-semibold">Người tham dự ({participants.length})</div>
                        <div className="mt-2 text-sm text-slate-500">WS: {wsStatus}</div>
                        <div className="mt-1 text-xs text-slate-400">Sent: {sendCount}</div>
                    </div>

                    <div className="px-3 pb-4 space-y-2">
                        {participants.map((p) => {
                            const active = p.sid === selectedSid;
                            const errCount = errorsBySid[p.sid]?.length ?? 0;
                            return (
                                <button
                                    key={p.sid}
                                    type="button"
                                    onClick={() => setSelectedSid(p.sid)}
                                    className={[
                                        "w-full rounded-lg px-3 py-2 text-left border",
                                        active
                                            ? "bg-indigo-600 text-white border-indigo-600"
                                            : "bg-white text-slate-800 border-slate-200 hover:bg-slate-50",
                                    ].join(" ")}
                                >
                                    <div className="flex items-center justify-between">
                                        <span className="font-medium truncate">{p.name}</span>
                                        <span className={active ? "text-white/90" : "text-slate-500"}>{errCount}</span>
                                    </div>
                                </button>
                            );
                        })}

                        {participants.length === 0 && (
                            <div className="text-sm text-slate-500 px-2 py-2">
                                Chưa có người tham gia (hoặc chưa ai bật camera).
                            </div>
                        )}
                    </div>
                </aside>

                {/* RIGHT: ảnh lỗi */}
                <main className="min-w-0">
                    <div className="bg-indigo-700 text-white px-6 py-5">
                        <div className="text-2xl font-semibold">Bảng lỗi</div>
                        <div className="text-sm opacity-90">Tên phòng: {roomName}</div>
                    </div>

                    <div className="p-6">
                        {selectedSid && selectedErrors.length === 0 ? (
                            <div className="rounded-xl border border-slate-200 bg-slate-50 px-6 py-10 text-slate-600">
                                Chưa có ảnh lỗi cho người này (server cần trả JSON có <b>frame_id</b>, <b>sid</b>, <b>error</b>).
                            </div>
                        ) : null}

                        {selectedSid && selectedErrors.length > 0 ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {selectedErrors.map((it) => (
                                    <div key={it.frame_id} className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
                                        <div className="aspect-[16/10] bg-black">
                                            <img src={it.dataUrl} alt={`frame ${it.frame_id}`} className="h-full w-full object-cover" />
                                        </div>
                                        <div className="px-4 py-3">
                                            <div className="text-sm font-semibold text-slate-900">[{it.error}]</div>
                                            <div className="mt-1 text-xs text-slate-500">
                                                frame_id: {it.frame_id} • {new Date(it.at).toLocaleString()}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : null}
                    </div>
                </main>
            </div>
        </div>
    );
}
