"""Batch split service — scan folder, compute segments, run sequential trims.

Pure logic / threading layer. No tkinter imports. UI marshals callbacks via
self.after(0, ...) on the main thread.
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from typing import Callable

from config import (
    VIDEO_EXTENSIONS, EXPORT_FORMATS, QUALITY_PRESETS,
    SPLIT_OUTPUT_SUBFOLDER, BATCH_MIN_SEGMENT_SECONDS,
)
from services.ffmpeg_service import TrimJob, run_trim, get_metadata


# ── Status constants ────────────────────────────────────────────────
STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_SKIPPED = "skipped"
STATUS_FAILED = "failed"
STATUS_UNREADABLE = "unreadable"


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


@dataclass
class BatchSplitJob:
    """Top-level batch run state."""
    input_folder: str
    output_folder: str
    files: list[BatchFileEntry]
    config: SplitConfig
    cancel_event: threading.Event = field(default_factory=threading.Event)
    current_trim: TrimJob | None = None


# ── Folder scan ─────────────────────────────────────────────────────

class ScanError(RuntimeError):
    """Raised when the folder itself cannot be read (permissions, missing, etc.)."""


def scan_folder(path: str) -> list[BatchFileEntry]:
    """Find every video in `path`, probe metadata, return sorted entries.

    Corrupt or unreadable files become entries with `status=UNREADABLE`
    and a `meta_error` message — they don't abort the scan.

    Raises ScanError if the folder itself cannot be opened (caller distinguishes
    "empty folder" from "unreadable folder").
    """
    entries: list[BatchFileEntry] = []
    if not os.path.isdir(path):
        raise ScanError(f"Not a folder: {path}")

    try:
        items = list(os.scandir(path))
    except OSError as exc:
        raise ScanError(f"Cannot read folder ({exc.__class__.__name__}): {exc}") from exc

    for item in items:
        if not item.is_file():
            continue
        ext = os.path.splitext(item.name)[1].lower()
        if ext not in VIDEO_EXTENSIONS:
            continue

        entry = BatchFileEntry(path=item.path)
        try:
            meta = get_metadata(item.path)
            entry.duration = meta.duration
            if entry.duration <= 0:
                entry.meta_error = "zero or unknown duration"
                entry.status = STATUS_UNREADABLE
        except Exception as exc:
            entry.meta_error = str(exc)[:200]
            entry.status = STATUS_UNREADABLE
        entries.append(entry)

    entries.sort(key=lambda e: e.name.lower())
    return entries


# ── Segment math ────────────────────────────────────────────────────

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


# ── Output naming ───────────────────────────────────────────────────

def build_output_path(
    entry: BatchFileEntry, seg_idx: int, total: int,
    output_folder: str, ext: str,
) -> str:
    """`<basename>_part_<n>_of_<N>.<ext>`, zero-padded to width if N >= 10."""
    width = 2 if total >= 10 else 1
    name = f"{entry.basename}_part_{seg_idx + 1:0{width}d}_of_{total}{ext}"
    return os.path.join(output_folder, name)


# ── Runner ──────────────────────────────────────────────────────────

def run_batch(
    job: BatchSplitJob,
    on_file_start: Callable[[BatchFileEntry], None] | None = None,
    on_file_progress: Callable[[BatchFileEntry], None] | None = None,
    on_file_done: Callable[[BatchFileEntry], None] | None = None,
    on_batch_done: Callable[[BatchSplitJob, str], None] | None = None,
) -> None:
    """Process each file sequentially. Runs in a daemon thread.

    `on_batch_done(job, error)` — error is "" on success, "cancelled",
    or an error message.
    """

    def _worker() -> None:
        try:
            os.makedirs(job.output_folder, exist_ok=True)
        except OSError as exc:
            if on_batch_done:
                on_batch_done(job, f"Cannot create output folder: {exc}")
            return

        cfg = job.config
        ext = cfg.ext
        quality = cfg.quality

        for entry in job.files:
            if job.cancel_event.is_set():
                break

            if entry.status == STATUS_UNREADABLE:
                continue

            segments = compute_segments(entry.duration, cfg)
            entry.parts_total = len(segments)

            if not segments:
                entry.status = STATUS_SKIPPED
                entry.error = "shorter than chunk size"
                if on_file_done:
                    on_file_done(entry)
                continue

            entry.status = STATUS_RUNNING
            entry.parts_done = 0
            entry.progress = 0.0
            if on_file_start:
                on_file_start(entry)

            file_failed = False
            for idx, (start, end) in enumerate(segments):
                if job.cancel_event.is_set():
                    break

                out_path = build_output_path(
                    entry, idx, len(segments), job.output_folder, ext,
                )

                trim = TrimJob(
                    input_path=entry.path,
                    output_path=out_path,
                    start=start,
                    end=end,
                    copy_streams=quality["copy"],
                    crf=quality["crf"],
                    include_audio=cfg.include_audio,
                    video_filter=None,
                )
                job.current_trim = trim

                done_event = threading.Event()

                def _seg_progress(pct: float, _entry=entry, _idx=idx,
                                  _total=len(segments)) -> None:
                    base = (_idx / _total) * 100.0
                    seg_share = (pct / _total)
                    _entry.progress = min(100.0, base + seg_share)
                    if on_file_progress:
                        on_file_progress(_entry)

                def _seg_done(_job: TrimJob, _ev=done_event) -> None:
                    _ev.set()

                run_trim(trim, on_progress=_seg_progress, on_done=_seg_done)

                # Wait for this segment to complete (or cancel).
                # NOTE: this loop has no timeout — it depends on `run_trim`'s
                # try/finally guarantee that `on_done` (→ done_event.set()) is
                # ALWAYS called, even on subprocess crash. If ffmpeg_service.py
                # is ever refactored to skip on_done on some path, this will
                # spin forever. Keep that contract intact.
                while not done_event.wait(0.1):
                    if job.cancel_event.is_set():
                        trim.cancel_event.set()

                if trim.error and "cancel" not in trim.error.lower():
                    entry.error = trim.error[:200]
                    file_failed = True
                    break

                if job.cancel_event.is_set():
                    break

                entry.parts_done += 1

            job.current_trim = None

            if job.cancel_event.is_set():
                # Mark in-progress file back to pending? No — leave partial.
                # Just stop the loop. Per-file status stays "running" so
                # the UI can show "interrupted".
                entry.status = STATUS_FAILED if file_failed else STATUS_PENDING
                entry.error = entry.error or "cancelled"
                if on_file_done:
                    on_file_done(entry)
                break

            entry.status = STATUS_FAILED if file_failed else STATUS_DONE
            entry.progress = 100.0 if not file_failed else entry.progress
            if on_file_done:
                on_file_done(entry)

        if on_batch_done:
            if job.cancel_event.is_set():
                on_batch_done(job, "cancelled")
            else:
                on_batch_done(job, "")

    threading.Thread(target=_worker, daemon=True).start()


def default_output_folder(input_folder: str) -> str:
    return os.path.join(input_folder, SPLIT_OUTPUT_SUBFOLDER)
