import sys
import os
from pathlib import Path
import cv2
import json

sys.path.append(str(Path(__file__).resolve().parents[1] / ''))

from app.services.yolo_service import YOLOService
from app.services.facemesh_service import FaceMeshService
from app.utils.drawing import draw_detections, draw_facemesh_info


def annotate_image(img_path: str, out_path: str = None):
    img = cv2.imread(img_path)
    if img is None:
        print(json.dumps({"error": "cannot_read_image", "path": img_path}))
        return None

    y = YOLOService()
    f = FaceMeshService()

    detections = y.detect(img.copy())
    facemesh = f.process(img.copy())

    annotated = img.copy()
    draw_detections(annotated, detections)
    draw_facemesh_info(annotated, facemesh)

    if out_path is None:
        p = Path(img_path)
        out_dir = p.parent
        out_name = f"annotated_{p.name}"
        out_path = str(out_dir / out_name)

    cv2.imwrite(out_path, annotated)
    print(json.dumps({"out_path": out_path, "detections": detections, "facemesh": facemesh}, ensure_ascii=False))
    return out_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/annotate_image.py <image_path> [out_path]")
        sys.exit(1)

    img_path = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    annotate_image(img_path, out)
