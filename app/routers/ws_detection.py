from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import base64
import traceback
import cv2
import time

from ..services.yolo_service import YOLOService
from ..services.facemesh_service import FaceMeshService
from ..services.logic_service import check_cheating
from ..utils.image_converter import base64_to_cv2_image
from ..services.mysql_adapter import ensure_room, ensure_user, insert_session_log, increment_room_participants
import asyncio

router = APIRouter()

@router.websocket("/ws/detection")
async def websocket_detection(ws: WebSocket):
    await ws.accept()
    print("[WS] 🔗 Client connected to /ws/detection")
    
    yolo = YOLOService()
    facemesh = FaceMeshService()
    frame_count = 0
    start_time = time.time()
    room_id = None
    user_id = None
    participant_name = None
    joined_counted = False
    # Per-connection state for time-based violations
    face_absent_since = None
    NO_FACE_SECONDS = 10.0

    yaw_violation_start = None
    pitch_down_start = None
    pitch_up_start = None
    gaze_deviation_start = None
    mouth_talking_start = None
    BEHAVIOR_CONTINUOUS_SECONDS = 2.0

    try:
        while True:
            data = await ws.receive_text()
            frame_count += 1
            recv_time = time.time()
            
            payload = json.loads(data)
            # support handshake
            if payload.get('handshake'):
                hs = payload.get('handshake', {})
                room_name = hs.get('room')
                participant_name = hs.get('participant')
                try:
                    if room_name:
                        room_id = ensure_room(room_name, None)
                        print(f"[DB] ensured room {room_name} id={room_id}")
                        # ensure participant count field exists but don't increment yet
                        try:
                            # no-op ensure
                            pass
                        except Exception:
                            pass
                    if participant_name:
                        user_id = ensure_user(participant_name)
                        print(f"[DB] ensured user {participant_name} id={user_id}")
                        try:
                            # update user's last seen/joined
                            from ..services.mysql_adapter import update_user_lastseen
                            update_user_lastseen(user_id, participant_name)
                            # increment count by 1 only once per connection
                            if room_id and not joined_counted:
                                increment_room_participants(room_id, 1)
                                joined_counted = True
                        except Exception:
                            pass
                except Exception as e:
                    print(f"[DB] handshake error: {e}")

            img_b64 = payload.get('image')
            if not img_b64:
                print(f"[WS] ⚠️ Frame #{frame_count}: no image in payload")
                await ws.send_text(json.dumps({"error": "no image"}))
                continue

            print(f"[WS] 📥 Frame #{frame_count}: received {len(img_b64)} chars of base64 at {recv_time - start_time:.2f}s")

            img = base64_to_cv2_image(img_b64)
            if img is None:
                print(f"[WS] ⚠️ Frame #{frame_count}: failed to decode base64 to image")
                await ws.send_text(json.dumps({"error": "invalid_image"}))
                continue

            print(f"[WS] ✅ Frame #{frame_count}: decoded to image shape {img.shape}")

            # Run detectors
            det_start = time.time()
            detections = yolo.detect(img)
            fm = facemesh.process(img)
            logic = check_cheating(detections, fm, img)
            det_time = time.time() - det_start

            # --- Time-based / continuous checks (per-connection stateful) ---
            now = time.time()
            # face presence: consider 'person' detections or facemesh result
            person_dets = [d for d in detections if d.get('label') == 'person']
            face_present = (fm is not None and fm.get('head_pose')) or len(person_dets) > 0

            # No Face Detected (absent for > NO_FACE_SECONDS)
            if not face_present:
                if face_absent_since is None:
                    face_absent_since = now
                else:
                    if now - face_absent_since >= NO_FACE_SECONDS:
                        if 'identity:no_face' not in logic.get('reason', []):
                            logic.setdefault('reason', []).append('identity:no_face')
                            logic.setdefault('violations', []).append({'type': 'identity:no_face', 'duration_s': now - face_absent_since})
            else:
                face_absent_since = None

            # Behavioral continuous checks using facemesh head_pose, eye_gaze and mouth_opening
            if fm and fm.get('head_pose'):
                hp = fm.get('head_pose')
                yaw = hp.get('yaw')
                pitch = hp.get('pitch')

                # Yaw (looking away) threshold 30 degrees
                if yaw is not None and abs(yaw) > 30:
                    if yaw_violation_start is None:
                        yaw_violation_start = now
                    elif now - yaw_violation_start >= BEHAVIOR_CONTINUOUS_SECONDS:
                        if 'behavior:looking_away' not in logic.get('reason', []):
                            logic.setdefault('reason', []).append('behavior:looking_away')
                            logic.setdefault('violations', []).append({'type': 'behavior:looking_away', 'yaw': yaw, 'duration_s': now - yaw_violation_start})
                else:
                    yaw_violation_start = None

                # Pitch down (looking down) threshold 25 degrees
                if pitch is not None and pitch > 25:
                    if pitch_down_start is None:
                        pitch_down_start = now
                    elif now - pitch_down_start >= BEHAVIOR_CONTINUOUS_SECONDS:
                        if 'behavior:looking_down' not in logic.get('reason', []):
                            logic.setdefault('reason', []).append('behavior:looking_down')
                            logic.setdefault('violations', []).append({'type': 'behavior:looking_down', 'pitch': pitch, 'duration_s': now - pitch_down_start})
                else:
                    pitch_down_start = None

                # Pitch up (looking up) threshold -20 degrees (negative)
                if pitch is not None and pitch < -20:
                    if pitch_up_start is None:
                        pitch_up_start = now
                    elif now - pitch_up_start >= BEHAVIOR_CONTINUOUS_SECONDS:
                        if 'behavior:looking_up' not in logic.get('reason', []):
                            logic.setdefault('reason', []).append('behavior:looking_up')
                            logic.setdefault('violations', []).append({'type': 'behavior:looking_up', 'pitch': pitch, 'duration_s': now - pitch_up_start})
                else:
                    pitch_up_start = None

            else:
                # reset continuous head pose counters if no facemesh available
                yaw_violation_start = None
                pitch_down_start = None
                pitch_up_start = None

                # Fallback: use detections (eye/mouth) to detect gaze/mouth behavior when facemesh unavailable
                # Mouth talking fallback
                mouth_dets = [d for d in detections if (d.get('label') or '').lower() == 'mouth']
                if mouth_dets:
                    # consider mouth present if any mouth detection exists
                    if mouth_talking_start is None:
                        mouth_talking_start = now
                    elif now - mouth_talking_start >= BEHAVIOR_CONTINUOUS_SECONDS:
                        if 'behavior:talking' not in logic.get('reason', []):
                            logic.setdefault('reason', []).append('behavior:talking')
                            logic.setdefault('violations', []).append({'type': 'behavior:talking', 'method': 'detection_fallback', 'count': len(mouth_dets), 'duration_s': now - mouth_talking_start})
                else:
                    mouth_talking_start = None

                # Eye gaze fallback: if person bbox exists, check average eye x offset
                eye_dets = [d for d in detections if (d.get('label') or '').lower() == 'eye']
                gaze_flag = False
                if person_dets and eye_dets:
                    # use largest person bbox
                    best_person = max(person_dets, key=lambda d: (d.get('bbox') or [0,0,0,0])[2] * (d.get('bbox') or [0,0,0,0])[3])
                    px, py, pw, ph = best_person.get('bbox', [0,0,0,0])
                    if pw > 0:
                        eye_centers_x = []
                        for e in eye_dets:
                            ex, ey, ew, eh = e.get('bbox', [0,0,0,0])
                            eye_centers_x.append(ex + ew/2.0)
                        if eye_centers_x:
                            avg_eye_x = sum(eye_centers_x) / len(eye_centers_x)
                            person_center_x = px + pw/2.0
                            rel = (avg_eye_x - person_center_x) / float(pw)
                            # if eyes are significantly offset from center (>15% of face width) -> possible gaze deviation
                            if abs(rel) > 0.15:
                                gaze_flag = True

                if gaze_flag:
                    if gaze_deviation_start is None:
                        gaze_deviation_start = now
                    elif now - gaze_deviation_start >= BEHAVIOR_CONTINUOUS_SECONDS:
                        if 'behavior:gaze_deviation' not in logic.get('reason', []):
                            logic.setdefault('reason', []).append('behavior:gaze_deviation')
                            logic.setdefault('violations', []).append({'type': 'behavior:gaze_deviation', 'method': 'detection_fallback', 'rel_offset': rel, 'duration_s': now - gaze_deviation_start})
                else:
                    gaze_deviation_start = None

            # Eye gaze deviation: use fm['eye_gaze'] (best-effort) when head is relatively straight
            if fm:
                eye_gaze = fm.get('eye_gaze')
                head_yaw = None
                if fm.get('head_pose'):
                    head_yaw = fm.get('head_pose').get('yaw')

                if eye_gaze is not None and (head_yaw is None or abs(head_yaw) < 15) and abs(eye_gaze) > 15:
                    if gaze_deviation_start is None:
                        gaze_deviation_start = now
                    elif now - gaze_deviation_start >= BEHAVIOR_CONTINUOUS_SECONDS:
                        if 'behavior:gaze_deviation' not in logic.get('reason', []):
                            logic.setdefault('reason', []).append('behavior:gaze_deviation')
                            logic.setdefault('violations', []).append({'type': 'behavior:gaze_deviation', 'eye_gaze': eye_gaze, 'duration_s': now - gaze_deviation_start})
                else:
                    gaze_deviation_start = None

                # Mouth / talking detection: use fm['mouth_opening'] (best-effort)
                mouth_opening = fm.get('mouth_opening') if fm else None
                if mouth_opening is not None and mouth_opening > 0.25:
                    if mouth_talking_start is None:
                        mouth_talking_start = now
                    elif now - mouth_talking_start >= BEHAVIOR_CONTINUOUS_SECONDS:
                        if 'behavior:talking' not in logic.get('reason', []):
                            logic.setdefault('reason', []).append('behavior:talking')
                            logic.setdefault('violations', []).append({'type': 'behavior:talking', 'mouth_opening': mouth_opening, 'duration_s': now - mouth_talking_start})
                else:
                    mouth_talking_start = None

            # update overall status boolean
            logic['status'] = len(logic.get('violations', [])) > 0

            # Only return compact detection log to frontend (no images)
            response = {
                "detections": detections,
                "logic": logic,
                "_frame_id": frame_count,
                "_process_ms": int(det_time * 1000)
            }

            print(f"[WS] 🔍 Frame #{frame_count}: AI processing took {det_time*1000:.1f}ms, found {len(detections) if isinstance(detections, list) else 0} detections")

            # persist session_log only if logic indicates a violation
            try:
                if user_id and room_id and img_b64 and logic and logic.get('status'):
                    # build a compact detection field that records the violation reason(s)
                    # Build a compact violations summary string for DB storage
                    compact_reasons = []
                    for v in logic.get('violations', []):
                        if not isinstance(v, dict):
                            continue
                        t = v.get('type', '')
                        if t == 'identity:multiple_faces' and v.get('count'):
                            compact_reasons.append(f"{v.get('count')} person")
                        elif t == 'identity:no_face':
                            compact_reasons.append('no_face')
                        elif t == 'object:phone_usage':
                            compact_reasons.append('phone')
                        elif t == 'object:books_notes_usage':
                            compact_reasons.append('book')
                        elif t.startswith('behavior:'):
                            compact_reasons.append(t.split(':', 1)[1])
                        # skip hint entries
                        elif t.startswith('hint:'):
                            continue
                        else:
                            # fallback to type or stringified
                            compact_reasons.append(t or str(v))

                    compact_str = ', '.join(dict.fromkeys(compact_reasons)) if compact_reasons else ', '.join(logic.get('reason', []))

                    detection_json = {
                        # store only the compact violations string as requested
                        "violations": compact_str
                    }

                    # draw bounding boxes for violating detections on a copy of the image
                    try:
                        pic = base64.b64decode(img_b64)
                        import numpy as np
                        nparr = np.frombuffer(pic, np.uint8)
                        img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        out_img = img_cv.copy() if img_cv is not None else None

                        bboxes = []
                        # collect bbox(es) from violations
                        for v in logic.get('violations', []):
                            if isinstance(v, dict):
                                if 'detection' in v and isinstance(v['detection'], dict):
                                    bb = v['detection'].get('bbox')
                                    if bb:
                                        bboxes.append(bb)
                                elif 'detections' in v and isinstance(v['detections'], list):
                                    for dd in v['detections']:
                                        bb = dd.get('bbox')
                                        if bb:
                                            bboxes.append(bb)

                        # fallback: if no bboxes collected but there are detections, draw them
                        if not bboxes and detections:
                            for d in detections:
                                bb = d.get('bbox')
                                if bb:
                                    bboxes.append(bb)

                        pic_bytes = None
                        if out_img is not None and bboxes:
                            for bb in bboxes:
                                try:
                                    x, y, w, h = map(int, bb)
                                    cv2.rectangle(out_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                                except Exception:
                                    pass
                            # annotate reason text
                            try:
                                    # prefer compact violations string when available
                                    reason_text = detection_json.get('violations') or (",".join(logic.get('reason', [])) if isinstance(logic.get('reason', []), list) else str(logic.get('reason')))
                                    cv2.putText(out_img, reason_text or 'violation', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                            except Exception:
                                pass

                            ret, buf = cv2.imencode('.jpg', out_img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                            if ret:
                                pic_bytes = buf.tobytes()

                        # if we couldn't produce boxed image, fall back to original image bytes
                        if not pic_bytes:
                            pic_bytes = base64.b64decode(img_b64)

                        # schedule background write so we don't block websocket loop
                        asyncio.create_task(asyncio.to_thread(insert_session_log, user_id, participant_name or '', detection_json, pic_bytes, room_id))
                    except Exception as e:
                        print(f"[DB] failed to prepare violation image: {e}")
            except Exception as e:
                print(f"[DB] failed to schedule session_log write: {e}")

            await ws.send_text(json.dumps(response))
            print(f"[WS] 📤 Frame #{frame_count}: response sent")

    except WebSocketDisconnect:
        elapsed = time.time() - start_time
        print(f"[WS] 🔌 Client disconnected. Processed {frame_count} frames in {elapsed:.1f}s")
        # decrement participant count if we incremented earlier
        try:
            if joined_counted and room_id:
                # run decrement in background
                asyncio.create_task(asyncio.to_thread(increment_room_participants, room_id, -1))
        except Exception as e:
            print(f"[DB] failed to decrement participant count: {e}")
        return
    except Exception as e:
        tb = traceback.format_exc()
        print(f"[WS] ❌ Error: {e}\n{tb}")
        await ws.send_text(json.dumps({"error": "server_error", "detail": str(e)}))
