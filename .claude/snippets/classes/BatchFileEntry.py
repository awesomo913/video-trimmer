# From: services/batch_split_service.py:49
# One video in the batch — populated by scan, mutated by runner.

@dataclass
class BatchFileEntry:
    """One video in the batch — populated by scan, mutated by runner."""
    path: str
    duration: float = 0.0
    meta_error: str = ""
    status: str = STATUS_PENDING
    progress: float = 0.0        # 0-100, across all segments of this file
    parts_done: int = 0
    parts_total: int = 0
    error: str = ""

    @property
    def name(self) -> str:
        return os.path.basename(self.path)

    @property
    def basename(self) -> str:
        return os.path.splitext(self.name)[0]
