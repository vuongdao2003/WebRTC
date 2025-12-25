// src/api/detection.ts

export const DETECTION_WS_URL =
    process.env.NEXT_PUBLIC_DETECTION_WS_URL ?? "ws://127.0.0.1:8000/ws/detection";

export type DetectionResult = {
    // server nên trả về ít nhất 2 field này để client map lại ảnh
    frame_id?: number;
    sid?: string;

    // yêu cầu mới của bạn: trả về error + frameID
    error?: string | null;

    // các field khác (tuỳ server)
    detections?: any[];
    facemesh?: any;
    logic?: { cheating?: boolean; reason?: string };

    [key: string]: any;
};

export type DetectionFramePayload = {
    image: string; // base64 (không có prefix data:image/..)
    sid: string;
    frame_id: number;
    name?: string;
};

export type DetectionClientOptions = {
    url?: string;
    debug?: boolean;
    onOpen?: () => void;
    onClose?: (ev: CloseEvent) => void;
    onError?: (ev: Event) => void;
    onMessage?: (data: DetectionResult) => void;
};

export class DetectionClient {
    private ws: WebSocket | null = null;
    private url: string;
    private opts: DetectionClientOptions;

    status: "idle" | "connecting" | "open" | "closed" | "error" = "idle";

    constructor(opts: DetectionClientOptions = {}) {
        this.opts = opts;
        this.url = opts.url ?? DETECTION_WS_URL;
    }

    connect() {
        if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
            return;
        }

        this.status = "connecting";
        const ws = new WebSocket(this.url);
        this.ws = ws;

        ws.onopen = () => {
            this.status = "open";
            if (this.opts.debug) console.log("[detection] socket opened:", this.url);
            this.opts.onOpen?.();
        };

        ws.onerror = (ev) => {
            this.status = "error";
            if (this.opts.debug) console.error("[detection] socket error", ev);
            this.opts.onError?.(ev);
        };

        ws.onclose = (ev) => {
            this.status = "closed";
            if (this.opts.debug) console.log("[detection] socket closed", ev);
            this.opts.onClose?.(ev);
        };

        ws.onmessage = (evt) => {
            try {
                const data = JSON.parse(evt.data) as DetectionResult;
                if (this.opts.debug) console.log("[detection] message", data);
                this.opts.onMessage?.(data);
            } catch (err) {
                if (this.opts.debug) console.error("[detection] parse error", err, evt.data);
            }
        };
    }

    close() {
        const ws = this.ws;
        this.ws = null;
        this.status = "closed";

        if (!ws) return;

        try {
            // tránh spam error khi StrictMode unmount lúc CONNECTING
            if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
                ws.close();
            }
        } catch { }
    }

    sendFrame(payload: DetectionFramePayload) {
        const ws = this.ws;
        if (!ws || ws.readyState !== WebSocket.OPEN) return;

        ws.send(JSON.stringify(payload));
    }

    // send handshake to register room/participant on server-side
    sendHandshake(room: string, participant: string) {
        const ws = this.ws;
        if (!ws || ws.readyState !== WebSocket.OPEN) return;
        const payload = { handshake: { room, participant } };
        try {
            ws.send(JSON.stringify(payload));
        } catch (e) {
            if (this.opts.debug) console.error('[detection] sendHandshake failed', e);
        }
    }
}

export function createDetectionClient(opts: DetectionClientOptions = {}) {
    return new DetectionClient(opts);
}
