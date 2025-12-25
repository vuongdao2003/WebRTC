"use client";

import { useMemo } from "react";
import { useSearchParams } from "next/navigation";
import AiRoomClient from "./AiRoomClient";

export default function AiPage() {
    const sp = useSearchParams();
    const room = sp.get("room") ?? "";
    const name = sp.get("name") ?? "";

    // tạo identity AI ổn định (1 lần)
    const aiIdentity = useMemo(() => {
        const suffix = Math.random().toString(16).slice(2, 8);
        return (name || "user") + `_ai-${suffix}`;
    }, [name]);

    if (!room) {
        return (
            <div className="min-h-screen flex items-center justify-center text-slate-600">
                Thiếu query ?room=...
            </div>
        );
    }

    return <AiRoomClient roomName={room} displayName={aiIdentity} />;
}
