import cv2
from typing import List, Dict


def draw_detections(img, detections: List[Dict]):
    for d in detections:
        x, y, w, h = d.get('bbox', [0, 0, 0, 0])
        label = d.get('label', '')
        conf = d.get('confidence', 0)
        color = (0, 255, 0)
        cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
        text = f"{label} {conf:.2f}"
        cv2.putText(img, text, (x, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)


def draw_facemesh_info(img, facemesh_result: Dict):
    if not facemesh_result:
        return

    hp = facemesh_result.get('head_pose', {})
    gaze = facemesh_result.get('gaze_direction', '')
    text = f"yaw:{hp.get('yaw',0):.1f} pitch:{hp.get('pitch',0):.1f} gaze:{gaze}"
    cv2.putText(img, text, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
