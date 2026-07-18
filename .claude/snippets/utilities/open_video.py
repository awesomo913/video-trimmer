# From: services/video_service.py:67
# Open a video file and return populated VideoState.

def open_video(path: str) -> VideoState:
    """Open a video file and return populated VideoState."""
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {path}")

    fc = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    dur = fc / fps if fps > 0 else 0.0

    return VideoState(
        path=path, cap=cap,
        frame_count=fc, fps=fps,
        width=w, height=h, duration=dur,
        trim_start=0.0, trim_end=dur,
    )
