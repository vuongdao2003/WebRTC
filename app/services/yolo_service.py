import cv2
import requests
from ..config import settings

class YOLOService:
    def __init__(self):
        self.model = settings.ROBOFLOW_MODEL       
        self.api_key = settings.ROBOFLOW_API_KEY    
        self.imgsz = settings.DETECT_IMG_SIZE       

        if not self.model:
            raise ValueError("ROBOFLOW_MODEL chưa được cấu hình!")

        if not self.api_key:
            raise ValueError("ROBOFLOW_API_KEY chưa được cấu hình!")

        self.url = f"https://detect.roboflow.com/{self.model}"

    def detect(self, img):

        detections = []

        ret, buf = cv2.imencode(".jpg", img)
        if not ret:
            return detections

        try:
            response = requests.post(
                self.url,
                params={"api_key": self.api_key},
                files={"file": ("image.jpg", buf.tobytes(), "image/jpeg")},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            for p in data.get("predictions", []):
                x = int(p["x"] - p["width"] / 2)
                y = int(p["y"] - p["height"] / 2)

                detections.append({
                    "label": p["class"],
                    "confidence": p["confidence"],
                    "bbox": [
                        x,
                        y,
                        int(p["width"]),
                        int(p["height"])
                    ]
                })

        except Exception as e:
            print("Roboflow error:", e)
            return detections

        return detections
