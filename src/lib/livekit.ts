// src/lib/livekit.ts
export async function fetchLivekitToken(roomName: string, participantName: string) {
    // Use NEXT_PUBLIC_API_BASE_URL if provided and not pointing to localhost;
    // otherwise use a relative path so requests go to the same origin and can
    // be proxied by the Next dev server. This avoids browser blocking when
    // the page is opened on a network IP but the backend is on loopback.
    const base = process.env.NEXT_PUBLIC_API_BASE_URL || "";
    const url = (base && !base.includes("localhost")) ? `${base}/token` : `/token`;
    console.log("Fetching token from:", url, { roomName, participantName });
    
    try {
        const res = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ roomName, participantName }),
        });
        
        console.log("Token response status:", res.status);
        
        if (!res.ok) {
            const errorText = await res.text();
            console.error("Token API error response:", errorText);
            throw new Error(`Token API error ${res.status}: ${errorText}`);
        }
        
        const data = (await res.json()) as { token: string };
        console.log("Token response data:", data);
        
        if (!data?.token) throw new Error("No token in response");
        return data.token;
    } catch (error) {
        console.error("fetchLivekitToken error:", error);
        throw error;
    }
}


export async function createRoomViaApi(
    roomName: string,
    options?: { maxParticipants?: number; metadata?: string }
) {
    const base = process.env.NEXT_PUBLIC_API_BASE_URL!;
    const res = await fetch(`${base}/rooms`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ roomName, ...options }),
    });
    if (!res.ok) throw new Error(`Create room error ${res.status}`);

    return true;
}
