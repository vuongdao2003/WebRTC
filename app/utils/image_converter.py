import base64
import cv2
import numpy as np
from typing import Tuple


def base64_to_cv2_image(b64_string: str) -> np.ndarray:
    if b64_string.startswith("data:"):
        b64_string = b64_string.split(',', 1)[1]

    b = base64.b64decode(b64_string)
    arr = np.frombuffer(b, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img


def cv2_to_jpeg_bytes(img: np.ndarray, quality: int = 80) -> bytes:
    params = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    ret, buf = cv2.imencode('.jpg', img, params)
    if not ret:
        return b''
    return buf.tobytes()

