// src/app/room/[roomId]/page.tsx

import RoomClient from "./RoomClient";

type RoomPageProps = {
    params: Promise<{ roomId: string }>;
    searchParams: Promise<{ name?: string }>;
};

export default async function RoomPage(props: RoomPageProps) {
    const { roomId: rawRoomId } = await props.params;
    const { name: rawName } = await props.searchParams;

    const roomName = decodeURIComponent(rawRoomId);
    const displayName =
        typeof rawName === "string" && rawName.trim().length > 0
            ? rawName.trim()
            : "Guest";

    return <RoomClient roomName={roomName} displayName={displayName} />;
}
