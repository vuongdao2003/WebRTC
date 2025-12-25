"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { LiveKitRoom, RoomAudioRenderer } from "@livekit/components-react";
import "@livekit/components-styles";

import { fetchLivekitToken } from "@/lib/livekit";
import { defaultLiveKitOptions } from "@/lib/livekitOptions";
import ConferenceLayout from "@/components/features/rtc/ConferenceLayout";

type RoomClientProps = {
    roomName: string; 
    displayName: string; 
};

type Status = "loading" | "ready" | "error";

export default function RoomClient({ roomName, displayName }: RoomClientProps) {
    const router = useRouter();
    const serverUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL!;
    const [token, setToken] = useState<string | null>(null);
    const [status, setStatus] = useState<Status>("loading");
    const [error, setError] = useState<string | null>(null);

    // Lấy token từ backend
    useEffect(() => {
        let cancelled = false;

        (async () => {
            try {
                setStatus("loading");
                const t = await fetchLivekitToken(roomName, displayName);
                if (!cancelled) {
                    setToken(t);
                    setStatus("ready");
                }
            } catch (e) {
                console.error(e);
                if (!cancelled) {
                    setError("Không lấy được token phòng.");
                    setStatus("error");
                }
            }
        })();

        return () => {
            cancelled = true;
        };
    }, [roomName, displayName]);

    function handleDisconnected() {
        router.push("/rtc");
    }

    if (status === "loading") {
        return (
            <div className="flex h-[100dvh] items-center justify-center bg-black text-white">
                Đang vào phòng...
            </div>
        );
    }

    if (status === "error" || !token) {
        return (
            <div className="flex h-[100dvh] flex-col items-center justify-center gap-4 bg-black text-white">
                <p>{error ?? "Không thể vào phòng."}</p>
                <button
                    onClick={() => router.push("/rtc")}
                    className="rounded-md bg-white/10 px-4 py-2 text-sm hover:bg-white/20"
                >
                    Quay lại trang tạo / tham gia phòng
                </button>
            </div>
        );
    }

    return (
        <LiveKitRoom
            token={token}
            serverUrl={serverUrl}
            connect
            video
            audio
            options={defaultLiveKitOptions}
            onDisconnected={handleDisconnected}
            data-lk-theme="default"
            style={{ height: "100dvh" }}
        >
            {/* ✅ Khung hiển thị camera + tên phòng + control bar */}
            <ConferenceLayout roomId={roomName} displayName={displayName} />

            {/* ✅ Phát toàn bộ audio trong phòng */}
            <RoomAudioRenderer />
        </LiveKitRoom>
    );
}
