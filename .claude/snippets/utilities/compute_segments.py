# From: services/batch_split_service.py:130
# Return (start, end) pairs in seconds. Empty list = skip this file.

def compute_segments(duration: float, config: SplitConfig) -> list[tuple[float, float]]:
    """Return (start, end) pairs in seconds. Empty list = skip this file."""
    if duration <= 0:
        return []

    if config.mode == "equal":
        n = max(1, int(config.n_parts))
        seg = duration / n
        segments: list[tuple[float, float]] = []
        for i in range(n):
            start = i * seg
            end = duration if i == n - 1 else (i + 1) * seg
            segments.append((start, end))
        return segments

    if config.mode == "duration":
        chunk = max(BATCH_MIN_SEGMENT_SECONDS, float(config.chunk_seconds))
        if duration < chunk:
            # Too short → skip in duration mode
            return []
        segments = []
        i = 0
        while i * chunk < duration:
            start = i * chunk
            end = min((i + 1) * chunk, duration)
            segments.append((start, end))
            i += 1
        return segments

    return []
