# From: services/ffmpeg_service.py:16

@dataclass
class VideoMeta:
    path: str = ""
    duration: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 0.0
    codec: str = ""
    audio_codec: str = ""
    bitrate: int = 0
    file_size: int = 0
    format_name: str = ""

    @property
    def resolution(self) -> str:
        return f"{self.width}x{self.height}"

    @property
    def duration_str(self) -> str:
        return format_time(self.duration)

    @property
    def size_str(self) -> str:
        mb = self.file_size / (1024 * 1024)
        if mb >= 1024:
            return f"{mb / 1024:.1f} GB"
        return f"{mb:.1f} MB"
