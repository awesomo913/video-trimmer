# From: services/video_service.py:17
# Shared mutable state for the currently loaded video.

@dataclass
class VideoState:
    """Shared mutable state for the currently loaded video."""
    path: str = ""
    cap: cv2.VideoCapture | None = field(default=None, repr=False)
    frame_count: int = 0
    fps: float = 0.0
    width: int = 0
    height: int = 0
    duration: float = 0.0
    current_frame: int = 0

    # Trim points (in seconds)
    trim_start: float = 0.0
    trim_end: float = 0.0

    # Edit transforms (preview + export): crop = inset % per edge (0–50)
    crop_enabled: bool = False
    crop_left_pct: float = 0.0
    crop_top_pct: float = 0.0
    crop_right_pct: float = 0.0
    crop_bottom_pct: float = 0.0
    rotation_cw: int = 0  # 0, 90, 180, 270 clockwise
    flip_horizontal: bool = False
    flip_vertical: bool = False

    @property
    def current_time(self) -> float:
        if self.fps <= 0:
            return 0.0
        return self.current_frame / self.fps

    @property
    def loaded(self) -> bool:
        return self.cap is not None and self.cap.isOpened()

    def time_to_frame(self, t: float) -> int:
        return max(0, min(int(t * self.fps), self.frame_count - 1))

    def frame_to_time(self, f: int) -> float:
        if self.fps <= 0:
            return 0.0
        return f / self.fps

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
