import cv2
import numpy as np

def detect_face_center_x(video_path: str, start_time: float, duration: float, sample_rate_sec: float = 0.5) -> float:
    """
    Samples frames from the video to find the speaker's horizontal center (0.0 to 1.0).
    Uses OpenCV Haar Cascade detector.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0.5  # default to center

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1920.0
    start_frame = int(start_time * fps)
    total_frames = int(duration * fps)
    step = max(1, int(fps * sample_rate_sec))

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    face_x_coords = []
    face_cascade_path = "models/haarcascade_frontalface_default.xml"
    cascade = None
    try:
        cascade = cv2.CascadeClassifier(face_cascade_path)
    except Exception:
        pass

    frame_idx = 0
    while frame_idx < total_frames:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % step == 0 and cascade is not None:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=4, minSize=(60, 60))
            if len(faces) > 0:
                largest = max(faces, key=lambda f: f[2] * f[3])
                fx, fy, fw, fh = largest
                center_x = (fx + fw / 2.0) / width
                face_x_coords.append(center_x)

        frame_idx += 1

    cap.release()

    if face_x_coords:
        return float(np.median(face_x_coords))
    return 0.5


def build_layout_filter(layout_mode: str, video_path: str = None, start_time: float = 0.0, duration: float = 0.0) -> tuple[str, bool, int, int]:
    """
    Returns:
    (filter_string, is_complex_filter, output_width, output_height)
    """
    # 1. 9:16 Vertical (Blurred Background)
    if layout_mode == "9:16_blurred":
        f = "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg];[0:v]scale=1080:-2[fg];[bg][fg]overlay=0:(H-h)/2"
        return f, True, 1080, 1920

    # 2. 9:16 Vertical (Smart Face Center)
    elif layout_mode == "9:16_face":
        center_ratio = 0.5
        if video_path and duration > 0:
            center_ratio = detect_face_center_x(video_path, start_time, duration)
        f = (
            f"crop=w=ih*9/16:h=ih:"
            f"x='max(0, min(iw-ow, {center_ratio:.3f}*iw - ow/2))':y=0,"
            f"scale=1080:1920"
        )
        return f, False, 1080, 1920

    # 3. 9:16 Vertical (Split-Screen / Top Video & Bottom Ambient)
    elif layout_mode == "9:16_split":
        f = (
            "[0:v]scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[top];"
            "[0:v]scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960,boxblur=20:5[bot];"
            "[top][bot]vstack"
        )
        return f, True, 1080, 1920

    # 4. 1:1 Square (Social Feed)
    elif layout_mode == "1:1_square":
        f = "[0:v]scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080,boxblur=25:5[bg];[0:v]scale=1080:-2[fg];[bg][fg]overlay=0:(H-h)/2"
        return f, True, 1080, 1080

    # 5. 4:5 Portrait (Instagram / Facebook)
    elif layout_mode == "4:5_portrait":
        f = "[0:v]scale=1080:1350:force_original_aspect_ratio=increase,crop=1080:1350,boxblur=25:5[bg];[0:v]scale=1080:-2[fg];[bg][fg]overlay=0:(H-h)/2"
        return f, True, 1080, 1350

    # 6. 16:9 Original Landscape (No crop)
    else:
        return "scale=1920:-2", False, 1920, 1080
