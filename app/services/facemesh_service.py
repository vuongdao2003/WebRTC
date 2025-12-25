import cv2
import numpy as np
import mediapipe as mp
import time

class FaceMeshService:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Load Haar Cascades MỘT LẦN duy nhất tại đây để tối ưu hiệu năng
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
        
        # Định nghĩa model 3D chuẩn của khuôn mặt (đơn vị tùy ý, thường là mm)
        # Thứ tự: Mũi, Cằm, Góc mắt trái, Góc mắt phải, Khóe miệng trái, Khóe miệng phải
        self.model_points = np.array([
            (0.0, 0.0, 0.0),             # Nose tip
            (0.0, -330.0, -65.0),        # Chin
            (-225.0, 170.0, -135.0),     # Left eye left corner
            (225.0, 170.0, -135.0),      # Right eye right corner
            (-150.0, -150.0, -125.0),    # Left Mouth corner
            (150.0, -150.0, -125.0)      # Right mouth corner
        ], dtype=np.float64)

    def process(self, img):
        h, w, c = img.shape
        
        # --- PHASE 1: Try MediaPipe (Chính xác cao) ---
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result = self.face_mesh.process(rgb)

        if result and result.multi_face_landmarks:
            face_landmarks = result.multi_face_landmarks[0]
            
            # Lấy các điểm quan trọng tương ứng với model 3D
            # Index MediaPipe: 1 (Mũi), 152 (Cằm), 33 (Mắt trái), 263 (Mắt phải), 61 (Miệng trái), 291 (Miệng phải)
            image_points = np.array([
                (face_landmarks.landmark[1].x * w, face_landmarks.landmark[1].y * h),
                (face_landmarks.landmark[152].x * w, face_landmarks.landmark[152].y * h),
                (face_landmarks.landmark[263].x * w, face_landmarks.landmark[263].y * h), # Lưu ý: MP trái phải ngược với ảnh
                (face_landmarks.landmark[33].x * w, face_landmarks.landmark[33].y * h),
                (face_landmarks.landmark[291].x * w, face_landmarks.landmark[291].y * h),
                (face_landmarks.landmark[61].x * w, face_landmarks.landmark[61].y * h)
            ], dtype=np.float64)

            head_pose = self.solve_pose_pnp(image_points, (h, w))
            
            if head_pose:
                # compute simple mouth opening metric and try to estimate eye gaze
                mouth_opening = None
                eye_gaze = None
                try:
                    # mouth vertical (upper/lower lip) and horizontal (corners)
                    upper_lip = face_landmarks.landmark[13]
                    lower_lip = face_landmarks.landmark[14]
                    left_mouth = face_landmarks.landmark[61]
                    right_mouth = face_landmarks.landmark[291]

                    mouth_vert = abs((upper_lip.y - lower_lip.y) * h)
                    mouth_horiz = abs((left_mouth.x - right_mouth.x) * w)
                    if mouth_horiz > 1:
                        mouth_opening = float(mouth_vert / mouth_horiz)
                    else:
                        mouth_opening = 0.0

                except Exception:
                    mouth_opening = None

                try:
                    # Attempt to estimate simple eye gaze using iris landmarks when available
                    # MediaPipe iris landmark indices are not guaranteed in all models/environments,
                    # so this is best-effort and wrapped in try/except.
                    # Typical iris indexes: left ~ 468-472, right ~ 473-477 (may vary).
                    # We'll try to use one representative landmark per eye.
                    left_iris = None
                    right_iris = None
                    if len(face_landmarks.landmark) > 470:
                        left_iris = face_landmarks.landmark[468]
                        right_iris = face_landmarks.landmark[473]

                    if left_iris and right_iris:
                        # compute relative x position of irises vs eye centers
                        left_eye_center_x = face_landmarks.landmark[33].x
                        right_eye_center_x = face_landmarks.landmark[263].x
                        # positive -> looking right, negative -> looking left (viewer perspective)
                        eye_gaze = ((left_iris.x - left_eye_center_x) + (right_iris.x - right_eye_center_x)) / 2.0
                        # scale to degrees-ish estimate by multiplying
                        eye_gaze = float(eye_gaze * 100.0)
                    else:
                        eye_gaze = None
                except Exception:
                    eye_gaze = None

                return {
                    "head_pose": head_pose,
                    "gaze_direction": self.estimate_gaze(head_pose['yaw']),
                    "method": "mediapipe_pnp",
                    "mouth_opening": mouth_opening,
                    "eye_gaze": eye_gaze
                }

        # --- PHASE 2: Fallback Haar Cascade (Kém chính xác hơn) ---
        return self.process_fallback(img)

    def solve_pose_pnp(self, image_points, img_size):
        h, w = img_size
        focal_length = w
        center = (w / 2, h / 2)
        
        # Ma trận camera giả định
        camera_matrix = np.array(
            [[focal_length, 0, center[0]],
             [0, focal_length, center[1]],
             [0, 0, 1]], dtype="double"
        )
        dist_coeffs = np.zeros((4, 1)) # Giả sử không có biến dạng thấu kính

        # Giải bài toán PnP
        success, rotation_vector, translation_vector = cv2.solvePnP(
            self.model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
        )

        if not success:
            return None

        # Chuyển đổi Rotation Vector sang Euler Angles
        rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
        proj_matrix = np.hstack((rotation_matrix, translation_vector))
        euler_angles = cv2.decomposeProjectionMatrix(proj_matrix)[6]

        pitch, yaw, roll = [element.item() for element in euler_angles]
        
        # Hiệu chỉnh lại dấu (tùy thuộc vào hệ quy chiếu mong muốn)
        # Thông thường: Pitch (nhìn lên/xuống), Yaw (trái/phải), Roll (nghiêng đầu)
        return {"pitch": pitch, "yaw": yaw, "roll": roll}

    def process_fallback(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Dùng model đã load sẵn trong __init__
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5)
        
        if len(faces) > 0:
            # Tìm thấy mặt trực diện -> Coi như đang nhìn thẳng (Yaw ~ 0)
            return {
                "head_pose": {"yaw": 0.0, "pitch": 0.0, "roll": 0.0},
                "gaze_direction": "forward",
                "method": "fallback_frontal"
            }
            
        # Nếu không thấy mặt trực diện, thử tìm mặt nghiêng (Profile)
        profiles = self.profile_cascade.detectMultiScale(gray, 1.1, 5)
        if len(profiles) > 0:
            # Logic: Nếu tìm thấy profile face, chắc chắn đang quay đầu mạnh
            # Cần xác định quay trái hay phải dựa vào vị trí
            (x, y, w, h) = profiles[0]
            center_x = x + w//2
            img_center = img.shape[1] // 2
            
            # Heuristic đơn giản: 
            # Profile detection không cho biết hướng quay, nhưng ta giả định
            # Dựa vào thuật toán profile thường detect mặt nhìn sang phải hoặc trái tùy file xml
            # Ở đây gán cứng đại diện
            yaw_estimate = 45.0 if center_x < img_center else -45.0
            
            return {
                "head_pose": {"yaw": yaw_estimate, "pitch": 0.0, "roll": 0.0},
                "gaze_direction": self.estimate_gaze(yaw_estimate),
                "method": "fallback_profile"
            }
            
        return None

    def estimate_gaze(self, yaw):
        if yaw is None: return "unknown"
        # Ngưỡng (Threshold) có thể tinh chỉnh
        if yaw > 20: return "looking_right" # Lưu ý hướng PnP có thể ngược với logic cũ
        if yaw < -20: return "looking_left"
        return "forward"