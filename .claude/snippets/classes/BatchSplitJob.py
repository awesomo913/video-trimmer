# From: services/batch_split_service.py:70
# Top-level batch run state.

@dataclass
class BatchSplitJob:
    """Top-level batch run state."""
    input_folder: str
    output_folder: str
    files: list[BatchFileEntry]
    config: SplitConfig
    cancel_event: threading.Event = field(default_factory=threading.Event)
    current_trim: TrimJob | None = None
