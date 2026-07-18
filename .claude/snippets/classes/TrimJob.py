# From: services/ffmpeg_service.py:111
# Holds state for a running trim operation.

@dataclass
class TrimJob:
    """Holds state for a running trim operation."""
    input_path: str
    output_path: str
    start: float
    end: float
    copy_streams: bool = True
    crf: int | None = None
    include_audio: bool = True
    video_filter: str | None = None
    process: subprocess.Popen | None = field(default=None, repr=False)
    cancel_event: threading.Event = field(default_factory=threading.Event)
    progress: float = 0.0
    done: bool = False
    error: str = ""
