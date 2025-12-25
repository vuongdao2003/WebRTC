"use client";

import Image from "next/image";
import type { ReactNode } from "react";

const pageBg = "#0F1115";

export default function RtcLayout({ children }: { children: ReactNode }) {
    return (
        <div
            className="min-h-[100dvh] w-full grid grid-cols-1 md:grid-cols-2"
            style={{ backgroundColor: pageBg }}
        >
            {/* Left hero */}
            <section className="relative hidden md:block">
                <Image
                    src="/login-bg.png"
                    alt="Eduva"
                    fill
                    className="object-cover"
                    priority
                />
                <div className="absolute inset-0 bg-[#2F327D] opacity-30" />
            </section>

            {/* Right content */}
            <section className="bg-[#F6F7FB] px-6 md:px-12 lg:px-16 py-14 md:py-20 flex justify-center items-start">
                <div className="w-full max-w-[560px]">{children}</div>
            </section>
        </div>
    );
}
