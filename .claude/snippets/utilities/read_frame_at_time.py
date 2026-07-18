# From: services/video_service.py:100
# Seek to a specific time and return the frame.

def read_frame_at_time(state: VideoState, time_sec: float) -> Image.Image | None:
    """Seek to a specific time and return the frame."""
    frame_num = state.time_to_frame(time_sec)
    return read_frame_at(state, frame_num)
