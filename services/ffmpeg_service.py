"""FFmpeg / FFprobe wrapper — metadata extraction and video trimming."""

from __future__ import annotations

import json
import os
import re
import subprocess
import threading
from dataclasses import dataclass, field
from typing import Callable

from config import FFMPEG_BIN, FFPROBE_BIN


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


def format_time(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:05.2f}"
    return f"{m:02d}:{s:05.2f}"


def parse_time(time_str: str) -> float:
    parts = time_str.strip().split(":")
    parts = [float(p) for p in parts]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return parts[0]


def get_metadata(path: str) -> VideoMeta:
    """Run ffprobe and return structured metadata."""
    cmd = [
        FFPROBE_BIN,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        path,
    ]
    result = subprocess.run(
        cmd, capture_output=True, text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr[:300]}")

    data = json.loads(result.stdout)
    fmt = data.get("format", {})
    streams = data.get("streams", [])

    video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})

    fps = 0.0
    r_frame_rate = video_stream.get("r_frame_rate", "0/1")
    if "/" in r_frame_rate:
        num, den = r_frame_rate.split("/")
        if int(den) > 0:
            fps = round(int(num) / int(den), 2)

    return VideoMeta(
        path=path,
        duration=float(fmt.get("duration", 0)),
        width=int(video_stream.get("width", 0)),
        height=int(video_stream.get("height", 0)),
        fps=fps,
        codec=video_stream.get("codec_name", "unknown"),
        audio_codec=audio_stream.get("codec_name", ""),
        bitrate=int(fmt.get("bit_rate", 0)),
        file_size=os.path.getsize(path),
        format_name=fmt.get("format_name", ""),
    )


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
    process: subprocess.Popen | None = field(default=None, repr=False)
    cancel_event: threading.Event = field(default_factory=threading.Event)
    progress: float = 0.0
    done: bool = False
    error: str = ""


def build_trim_cmd(job: TrimJob) -> list[str]:
    """Build the ffmpeg command list for a trim job."""
    cmd = [FFMPEG_BIN, "-y"]

    # Input seeking (fast) then precise trim
    cmd += ["-ss", str(job.start)]
    cmd += ["-i", job.input_path]
    cmd += ["-to", str(job.end - job.start)]

    if job.copy_streams:
        cmd += ["-c", "copy"]
    else:
        cmd += ["-c:v", "libx264", "-preset", "medium"]
        if job.crf is not None:
            cmd += ["-crf", str(job.crf)]
        if job.include_audio:
            cmd += ["-c:a", "aac", "-b:a", "192k"]

    if not job.include_audio:
        cmd += ["-an"]

    cmd += ["-avoid_negative_ts", "make_zero"]
    cmd += [job.output_path]
    return cmd


_PROGRESS_RE = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")


def run_trim(
    job: TrimJob,
    on_progress: Callable[[float], None] | None = None,
    on_done: Callable[[TrimJob], None] | None = None,
) -> None:
    """Run the trim in a background thread. Calls on_progress(0-100) and on_done(job)."""
    duration = job.end - job.start
    if duration <= 0:
        job.error = "End time must be after start time"
        job.done = True
        if on_done:
            on_done(job)
        return

    cmd = build_trim_cmd(job)

    def _worker():
        try:
            job.process = subprocess.Popen(
                cmd,
                stderr=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            for line in job.process.stderr:
                if job.cancel_event.is_set():
                    job.process.kill()
                    job.error = "Cancelled"
                    break
                match = _PROGRESS_RE.search(line)
                if match and duration > 0:
                    t = (int(match.group(1)) * 3600
                         + int(match.group(2)) * 60
                         + float(match.group(3)))
                    job.progress = min(100.0, (t / duration) * 100)
                    if on_progress:
                        on_progress(job.progress)

            job.process.wait()
            if not job.cancel_event.is_set() and job.process.returncode != 0:
                job.error = f"ffmpeg exited with code {job.process.returncode}"
        except Exception as exc:
            job.error = str(exc)
        finally:
            job.done = True
            job.progress = 100.0 if not job.error else job.progress
            if on_done:
                on_done(job)

    threading.Thread(target=_worker, daemon=True).start()
