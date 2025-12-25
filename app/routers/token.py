import os
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from livekit.api import AccessToken, VideoGrants, TokenVerifier, WebhookReceiver

load_dotenv()

SERVER_PORT = os.environ.get("SERVER_PORT", 8000)
LIVEKIT_API_KEY = os.environ.get("LIVEKIT_API_KEY", "devkey")
LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET", "secret")

router = APIRouter()

token_verifier = TokenVerifier(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
webhook_receiver = WebhookReceiver(token_verifier)
from ..services.mysql_adapter import ensure_room


@router.post("/token")
async def create_token(request: Request):
    body = await request.json()
    room_name = body.get("roomName")
    participant_name = body.get("participantName")

    if not room_name or not participant_name:
        raise HTTPException(status_code=400, detail="roomName and participantName are required")

    # Ensure the room exists in the DB (create per-room session table as side-effect)
    try:
        ensure_room(room_name, None)
    except Exception as e:
        # non-fatal for token issuance, but log for debugging
        print(f"[token] failed to ensure_room '{room_name}': {e}")

    token = (
        AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(participant_name)
        .with_grants(VideoGrants(room_join=True, room=room_name))
    )
    return {"token": token.to_jwt()}


@router.post("/livekit/webhook")
async def receive_webhook(request: Request):
    auth_token = request.headers.get("Authorization")

    if not auth_token:
        raise HTTPException(status_code=401, detail="Authorization header is required")

    try:
        event = webhook_receiver.receive((await request.body()).decode("utf-8"), auth_token)
        print("LiveKit Webhook:", event)
        # Try to ensure room exists when webhook contains room information.
        try:
            room_name = None
            # event may be a dict or an object depending on livekit version
            if isinstance(event, dict):
                # common shapes: {'room': {'name': '...'}}, or {'room': 'name'}
                if isinstance(event.get('room'), dict):
                    room_name = event.get('room', {}).get('name')
                else:
                    room_name = event.get('room') or event.get('roomName') or event.get('room_name')
            else:
                # object with attribute access
                room_attr = getattr(event, 'room', None)
                if room_attr:
                    room_name = getattr(room_attr, 'name', room_attr)

            if room_name:
                try:
                    ensure_room(room_name, None)
                except Exception as e:
                    print(f"[webhook] ensure_room failed for '{room_name}': {e}")
        except Exception as e:
            print(f"[webhook] failed to process event for ensuring room: {e}")
        return "ok"
    except:
        raise HTTPException(status_code=401, detail="Authorization header is not valid")
