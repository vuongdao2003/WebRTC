"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import Input from "@/components/ui/Input";

export default function CreateRoomForm() {
    const router = useRouter();

    const [name, setName] = useState("");
    const [roomId, setRoomId] = useState("");
    const [errorMsg, setErrorMsg] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    function onSubmit(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault();

        const n = name.trim();
        const r = roomId.trim();

        if (!n || !r) {
            setErrorMsg("Vui lòng nhập đầy đủ Tên hiển thị và Mã phòng.");
            return;
        }

        setErrorMsg(null);
        setLoading(true);
        router.push(`/room/${encodeURIComponent(r)}?name=${encodeURIComponent(n)}`);
    }

    return (
        <div className="w-full">
            <div className="text-center">
                <h2 className="text-3xl md:text-[34px] font-semibold text-black">
                    Tham gia phòng
                </h2>
                <p className="mt-3 text-base md:text-[17px] text-zinc-600">
                    Nhập tên hiển thị và mã phòng để tham gia.
                </p>
            </div>

            <form className="mt-10 space-y-7" onSubmit={onSubmit}>
                <div>
                    <label className="mb-2 block text-base md:text-lg font-medium text-black">
                        Tên hiển thị
                    </label>
                    <Input
                        placeholder="VD: Tùng"
                        className="h-12 rounded-full bg-white px-5 text-black placeholder:text-zinc-400"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                    />
                </div>

                <div>
                    <label className="mb-2 block text-base md:text-lg font-medium text-black">
                        Mã phòng
                    </label>
                    <Input
                        placeholder="VD: 88888888"
                        className="h-12 rounded-full bg-white px-5 text-black placeholder:text-zinc-400"
                        value={roomId}
                        onChange={(e) => setRoomId(e.target.value)}
                    />
                </div>

                {errorMsg && (
                    <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                        {errorMsg}
                    </div>
                )}

                <button
                    type="submit"
                    disabled={loading || !name.trim() || !roomId.trim()}
                    className="mx-auto block w-full max-w-[360px] rounded-full bg-[#2F327D] px-6 py-3 text-base font-semibold text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                >
                    {loading ? "Đang vào phòng..." : "Vào phòng"}
                </button>
            </form>
        </div>
    );


}
