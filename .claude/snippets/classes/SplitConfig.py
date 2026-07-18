# From: services/batch_split_service.py:30
# Per-batch configuration: how to split and how to encode.

@dataclass
class SplitConfig:
    """Per-batch configuration: how to split and how to encode."""
    mode: str = "equal"             # "equal" | "duration"
    n_parts: int = 4
    chunk_seconds: float = 60.0
    output_format: str = "MP4  (.mp4)"
    quality_key: str = "Copy (fastest, lossless)"
    include_audio: bool = True

    @property
    def ext(self) -> str:
        return EXPORT_FORMATS[self.output_format]["ext"]

    @property
    def quality(self) -> dict:
        return QUALITY_PRESETS[self.quality_key]
