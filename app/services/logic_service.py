def check_cheating(detections, facemesh_result, img=None):
    """Evaluate simple cheating rules and return structured violations.

    Returns a dict with:
    - status: bool (True if any violation)
    - reason: list of short strings
    - violations: list of dicts with detailed info (type, context)
    """
    reasons = []
    violations = []

    # Rule 1: multiple people detected
    person_dets = [d for d in detections if d.get("label") == "person"]
    person_count = len(person_dets)
    if person_count >= 2:
        reasons.append("identity:multiple_faces")
        violations.append({"type": "identity:multiple_faces", "count": person_count, "detections": person_dets})

    # Rule 2: prohibited objects (model only predicts these labels: phone, book)
    for d in detections:
        lbl = (d.get("label") or "").lower()
        if lbl == "phone":
            reasons.append("object:phone_usage")
            violations.append({"type": "object:phone_usage", "object": lbl, "detection": d})
        elif lbl == "book":
            reasons.append("object:books_notes_usage")
            violations.append({"type": "object:books_notes_usage", "object": lbl, "detection": d})

    # Include detection hints for eye/mouth presence (useful for fallback logic)
    eye_dets = [d for d in detections if (d.get("label") or "").lower() == "eye"]
    mouth_dets = [d for d in detections if (d.get("label") or "").lower() == "mouth"]
    if eye_dets:
        reasons.append("hint:eye_detected")
        violations.append({"type": "hint:eye_detected", "count": len(eye_dets), "detections": eye_dets})
    if mouth_dets:
        reasons.append("hint:mouth_detected")
        violations.append({"type": "hint:mouth_detected", "count": len(mouth_dets), "detections": mouth_dets})

    # Rule 3: immediate head-pose thresholds (per-frame)
    if facemesh_result and facemesh_result.get("head_pose"):
        hp = facemesh_result.get("head_pose")
        yaw = hp.get("yaw")
        pitch = hp.get("pitch")
        # Yaw (turning left/right) - immediate flag if extreme
        if yaw is not None and abs(yaw) > 45:
            reasons.append("behavior:extreme_yaw")
            violations.append({"type": "behavior:extreme_yaw", "yaw": yaw})
        # Pitch extreme (very low / very high) - immediate
        if pitch is not None:
            if pitch > 40:
                reasons.append("behavior:extreme_looking_down")
                violations.append({"type": "behavior:extreme_looking_down", "pitch": pitch})
            if pitch < -40:
                reasons.append("behavior:extreme_looking_up")
                violations.append({"type": "behavior:extreme_looking_up", "pitch": pitch})
    else:
        # If facemesh not available, try a simple image-based fallback using detections + edge asymmetry
        try:
            if img is not None and detections:
                # choose largest detection as subject
                best = max(detections, key=lambda d: d.get("bbox", [0,0,0,0])[2] * d.get("bbox", [0,0,0,0])[3])
                x, y, w, h = best.get("bbox", [0,0,0,0])
                import cv2
                import numpy as np
                ih, iw = img.shape[:2]
                x1 = max(0, int(x))
                y1 = max(0, int(y))
                x2 = min(iw, int(x + w))
                y2 = min(ih, int(y + h))
                if x2 - x1 > 10 and y2 - y1 > 10:
                    roi = img[y1:y2, x1:x2]
                    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                    edges = cv2.Canny(gray, 50, 150)
                    mid = edges.shape[1] // 2
                    left_sum = int(edges[:, :mid].sum())
                    right_sum = int(edges[:, mid:].sum())
                    total = left_sum + right_sum
                    if total > 1000:
                        asym = (left_sum - right_sum) / float(total)
                        # threshold for deciding turned head
                        if abs(asym) > 0.12:
                            # positive => more detail on left half => subject facing left (viewer)
                            yaw = 30.0 if asym > 0 else -30.0
                            reasons.append("looking_away_fallback")
                            violations.append({"type": "looking_away_fallback", "yaw": yaw, "asymmetry": asym, "detection": best})
        except Exception:
            pass

    return {
        "status": len(violations) > 0,
        "reason": reasons,
        "violations": violations,
    }
