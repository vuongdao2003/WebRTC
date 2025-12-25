"use client";

import { useEffect, useState } from "react";
import { LiveKitRoom } from "@livekit/components-react";
import "@livekit/components-styles";
import { fetchLivekitToken } from "@/lib/livekit";
import AiMonitorClient from "@/components/features/rtc/AiMonitorClient";

type Props = {
    roomName: string;
    displayName: string; // tên đã có suffix _ai-...
};

export default function AiRoomClient({ roomName, displayName }: Props) {
    const serverUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL!;
    const [token, setToken] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;

        (async () => {
            try {
                setError(null);
                const t = await fetchLivekitToken(roomName, displayName);
                if (!cancelled) setToken(t);
            } catch (e: any) {
                if (!cancelled) setError(e?.message ?? "Không lấy được token");
            }
        })();

        return () => {
            cancelled = true;
        };
    }, [roomName, displayName]);

    if (error) return <div className="p-6 text-red-500">{error}</div>;
    if (!token) return <div className="p-6 text-slate-500">Đang kết nối...</div>;

    return (
        <div className="h-screen w-screen">
            <LiveKitRoom
                serverUrl={serverUrl}
                token={token}
                connect
                audio={false}
                video={false}
                className="h-full w-full"
            >
                <AiMonitorClient roomName={roomName} displayName={displayName} />
            </LiveKitRoom>
        </div>
    );
}
