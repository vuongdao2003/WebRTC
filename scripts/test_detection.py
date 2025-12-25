import sys
import json
import cv2
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / ''))

from app.services.yolo_service import YOLOService
from app.services.facemesh_service import FaceMeshService
from app.services.logic_service import check_cheating
from scripts.annotate_image import annotate_image


def main(img_path: str):
    img = cv2.imread(img_path)
    if img is None:
        print(json.dumps({"error": "cannot_read_image", "path": img_path}))
        return

    y = YOLOService()
    f = FaceMeshService()

    detections = y.detect(img)
    facemesh = f.process(img)

    out = {
        "detections": detections,
        "facemesh": facemesh
    }
    # run logic check with fallback (pass image)
    logic = check_cheating(detections, facemesh, img)
    out["logic"] = logic
    print(json.dumps(out, indent=2, ensure_ascii=False))

    # Also create an annotated image next to the original file
    try:
        annotated_path = annotate_image(img_path)
        if annotated_path:
            print(json.dumps({"annotated_image": annotated_path}))
    except Exception as e:
        print(json.dumps({"annotate_error": str(e)}))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_detection.py <image_path>")
        sys.exit(1)
    main(sys.argv[1])
