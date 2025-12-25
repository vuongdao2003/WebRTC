"use client";

import { useEffect, useRef, useState } from "react";

type LocalPreviewProps = {
    audioOn: boolean;
    videoOn: boolean;
    onStream?: (stream: MediaStream | null) => void;
};

export default function LocalPreview({ audioOn, videoOn, onStream }: LocalPreviewProps) {
    const videoRef = useRef<HTMLVideoElement | null>(null);
    const [stream, setStream] = useState<MediaStream | null>(null);

    useEffect(() => {
        let activeStream: MediaStream | null = null;

        async function setup() {
            if (!audioOn && !videoOn) {
                if (activeStream) {
                    activeStream.getTracks().forEach((t) => t.stop());
                    activeStream = null;
                }
                setStream(null);
                onStream?.(null);
                return;
            }

            activeStream = await navigator.mediaDevices.getUserMedia({
                video: videoOn,
                audio: audioOn,
            });

            setStream(activeStream);
            onStream?.(activeStream);

            if (videoRef.current) {
                videoRef.current.srcObject = activeStream;
            }
        }

        setup().catch((err) => console.error("getUserMedia error", err));

        return () => {
            if (activeStream) {
                activeStream.getTracks().forEach((t) => t.stop());
            }
            onStream?.(null);
        };
    }, [audioOn, videoOn, onStream]);

    useEffect(() => {
        if (videoRef.current && stream) {
            videoRef.current.srcObject = stream;
        }
    }, [stream]);

    return (
        <div className="relative aspect-video w-full overflow-hidden rounded-xl border bg-black/80">
            <video
                ref={videoRef}
                autoPlay
                muted
                playsInline
                className="h-full w-full object-cover"
            />
            <div className="absolute left-2 top-2 rounded bg-white/80 px-2 py-1 text-xs text-black">
                Camera của bạn
            </div>
        </div>
    );
}
