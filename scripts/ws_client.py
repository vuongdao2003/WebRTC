import sys
import json
import base64
import cv2
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / ''))

import websocket
import time

def main(img_path: str, ws_url: str = 'ws://localhost:8000/ws/detection'):
    img = cv2.imread(img_path)
    if img is None:
        print(json.dumps({"error": "cannot_read_image", "path": img_path}))
        return

    ret, buf = cv2.imencode('.jpg', img)
    if not ret:
        print(json.dumps({"error": "encode_failed"}))
        return

    b64 = base64.b64encode(buf.tobytes()).decode()

    ws = websocket.create_connection(ws_url)
    # send handshake first to register room/participant
    handshake = json.dumps({"handshake": {"room": "test_room", "participant": "ws_client"}})
    ws.send(handshake)
    print("sent handshake")
    time.sleep(0.2)
    payload = json.dumps({"image": b64})
    ws.send(payload)
    resp = ws.recv()
    print(resp)
    ws.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/ws_client.py <image_path> [ws_url]")
        sys.exit(1)

    img_path = sys.argv[1]
    ws_url = sys.argv[2] if len(sys.argv) > 2 else 'ws://localhost:8000/ws/detection'
    main(img_path, ws_url)
