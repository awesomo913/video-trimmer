# From: services/video_service.py:87
# Seek to a specific frame and return it as a PIL Image.

def read_frame_at(state: VideoState, frame_num: int) -> Image.Image | None:
    """Seek to a specific frame and return it as a PIL Image."""
    if not state.loaded:
        return None
    state.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
    ret, frame = state.cap.read()
    if not ret:
        return None
    state.current_frame = frame_num
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)
