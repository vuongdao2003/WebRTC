// src/lib/livekitOptions.ts
import type { RoomOptions } from "livekit-client";
import { VideoPresets } from "livekit-client";

export const defaultLiveKitOptions: RoomOptions = {

    adaptiveStream: true,

    dynacast: true,

    publishDefaults: {
        simulcast: true,
        videoSimulcastLayers: [
            VideoPresets.h180, // Low   (180p)
            VideoPresets.h360, // Medium(360p)
            VideoPresets.h720, // High  (720p)
        ],
    },
};
