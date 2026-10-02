"""FFmpeg wrapper — metadata extraction and video trimming.

Only `ffmpeg` is used (never ffprobe): metadata is parsed from the banner that
`ffmpeg -i <file>` prints, so the single bundled binary is enough.
"""

from __future__ import annotations

import collections
import logging
import math
import os
import re
import subprocess
import threading
from collections.abc import Callable
from dataclasses import dataclass, field

from services.ffmpeg_locator import FFmpegNotFoundError, find_ffmpeg
from services.fsutil import same_file

log = logging.getLogger(__name__)

_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
MIN_CLIP_SECONDS = 0.04  # shorter than one frame at 25 fps: nothing useful to export
PROBE_TIMEOUT_SECONDS = 30


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
    def has_audio(self) -> bool:
        return bool(self.audio_codec)

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
    if not math.isfinite(seconds) or seconds < 0:
        seconds = 0.0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:05.2f}"
    return f"{m:02d}:{s:05.2f}"


def parse_time(time_str: str) -> float:
    """Parse `SS`, `MM:SS` or `HH:MM:SS(.ff)` into seconds. Raises ValueError if invalid."""
    parts = [float(p) for p in time_str.strip().split(":")]
    if not parts or len(parts) > 3 or any(not math.isfinite(p) or p < 0 for p in parts):
        raise ValueError(f"Not a valid time: {time_str!r}")
    total = 0.0
    for p in parts:
        total = total * 60 + p
    return total


# ── Metadata (parsed from `ffmpeg -i`) ─────────────────────────────

_DURATION_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")
_BITRATE_RE = re.compile(r"bitrate:\s*(\d+)\s*kb/s")
_INPUT_RE = re.compile(r"Input #0,\s*([^,]+(?:,[^,]+)*?),\s*from")
_STREAM_RE = re.compile(r"Stream #\d+:\d+[^:]*:\s*(Video|Audio):\s*(.*)")
_RES_RE = re.compile(r"(?<![\w.])(\d{2,5})x(\d{2,5})(?![\w.])")
_FPS_RE = re.compile(r"(\d+(?:\.\d+)?)\s*fps")
_TBR_RE = re.compile(r"(\d+(?:\.\d+)?)\s*tbr")
_ROTATION_RE = re.compile(r"rotation of (-?\d+(?:\.\d+)?) degrees")
_PAREN_RE = re.compile(r"\([^)]*\)|\[[^\]]*\]")


def parse_ffmpeg_info(text: str, path: str = "") -> VideoMeta:
    """Turn the stderr of `ffmpeg -i file` into a VideoMeta.

    Raises RuntimeError when the text has no recognisable media information.
    """
    dur = _DURATION_RE.search(text)
    meta = VideoMeta(path=path)
    if dur:
        meta.duration = (int(dur.group(1)) * 3600 + int(dur.group(2)) * 60
                         + float(dur.group(3)))
    br = _BITRATE_RE.search(text)
    if br:
        meta.bitrate = int(br.group(1)) * 1000
    fmt = _INPUT_RE.search(text)
    if fmt:
        meta.format_name = fmt.group(1).strip()

    have_video = False
    for line in text.splitlines():
        stream = _STREAM_RE.search(line)
        if not stream:
            continue
        kind, rest = stream.group(1), stream.group(2)
        if kind == "Audio":
            if not meta.audio_codec:
                meta.audio_codec = rest.split(",")[0].split()[0] if rest.strip() else ""
            continue
        if have_video or "attached pic" in line:
            continue
        have_video = True
        meta.codec = rest.split(",")[0].split()[0] if rest.strip() else "unknown"
        cleaned = _PAREN_RE.sub(" ", rest)
        res = _RES_RE.search(cleaned)
        if res:
            meta.width, meta.height = int(res.group(1)), int(res.group(2))
        fps = _FPS_RE.search(rest) or _TBR_RE.search(rest)
        if fps:
            meta.fps = round(float(fps.group(1)), 2)

    if not have_video and not meta.audio_codec:
        raise RuntimeError("No audio or video streams found in this file")

    rot = _ROTATION_RE.search(text)
    if rot and round(abs(float(rot.group(1)))) % 180 == 90:
        meta.width, meta.height = meta.height, meta.width
    return meta


def get_metadata(path: str) -> VideoMeta:
    """Read duration, size, codecs and frame rate of a media file."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")
    cmd = [find_ffmpeg(), "-hide_banner", "-nostdin", "-i", path]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
            stdin=subprocess.DEVNULL, timeout=PROBE_TIMEOUT_SECONDS,
            creationflags=_NO_WINDOW,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("ffmpeg took too long to read this file") from exc
    # ffmpeg exits non-zero here ("At least one output file must be specified");
    # the information we want is on stderr either way.
    try:
        meta = parse_ffmpeg_info(result.stderr, path)
    except RuntimeError as exc:
        raise RuntimeError(f"{exc}. ffmpeg said: {summarize_ffmpeg_error(result.stderr)}") from exc
    meta.file_size = os.path.getsize(path)
    return meta


# ── Trim jobs ──────────────────────────────────────────────────────


class TrimError(ValueError):
    """The requested trim cannot be done (bad times, bad destination)."""


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
    source_duration: float | None = None  # known length of the source, if any
    process: subprocess.Popen | None = field(default=None, repr=False)
    cancel_event: threading.Event = field(default_factory=threading.Event)
    progress: float = 0.0
    done: bool = False
    error: str = ""


def validate_trim(start: float, end: float,
                  source_duration: float | None = None) -> tuple[float, float]:
    """Check the trim range and return it, clamped to the source length.

    Raises TrimError with a plain-language message for in == out, reversed or
    non-finite times, or a start beyond the end of the video. An `end` past the
    end of the video is not an error; it is clamped.
    """
    if not (math.isfinite(start) and math.isfinite(end)):
        raise TrimError("Start and end must be real numbers")
    if start < 0:
        start = 0.0
    if end <= start:
        if end == start:
            raise TrimError("Start and end are the same, so the clip would be empty")
        raise TrimError("End time must be after start time")
    if source_duration is not None and source_duration > 0:
        if start >= source_duration:
            raise TrimError("Start is past the end of the video")
        end = min(end, source_duration)
    if end - start < MIN_CLIP_SECONDS:
        raise TrimError("The selected clip is shorter than one frame")
    return start, end


def _video_args(job: TrimJob, ext: str) -> list[str]:
    crf = job.crf if job.crf is not None else 23
    if ext == ".webm":
        return ["-c:v", "libvpx-vp9", "-crf", str(crf), "-b:v", "0",
                "-row-mt", "1", "-deadline", "good", "-cpu-used", "4"]
    return ["-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p"]


def _audio_args(job: TrimJob, ext: str) -> list[str]:
    if not job.include_audio:
        return ["-an"]
    # Edits force a video re-encode but "Copy" quality keeps the audio untouched,
    # except WebM, which cannot hold AAC/MP3.
    if job.copy_streams and ext != ".webm":
        return ["-c:a", "copy"]
    if ext == ".webm":
        return ["-c:a", "libopus", "-b:a", "128k"]
    return ["-c:a", "aac", "-b:a", "192k"]


def build_trim_cmd(job: TrimJob, start: float | None = None, end: float | None = None) -> list[str]:
    """Build the ffmpeg command for a trim job.

    Seeks on the input (fast), then writes `end - start` seconds. With stream
    copy the cut snaps to the keyframe at or before `start`.
    """
    start = job.start if start is None else start
    end = job.end if end is None else end
    ext = os.path.splitext(job.output_path)[1].lower()

    cmd = [find_ffmpeg(), "-hide_banner", "-nostdin", "-y",
           "-ss", f"{start:.3f}", "-i", job.input_path,
           "-t", f"{end - start:.3f}",
           # First choice of streams: every video and audio stream. Subtitle and
           # data tracks (common in .ts / phone footage) break many containers.
           "-map", "0:v", "-map", "0:a?"]

    reencode_video = bool(job.video_filter) or not job.copy_streams
    if reencode_video:
        if job.video_filter:
            cmd += ["-vf", job.video_filter]
        cmd += _video_args(job, ext)
    else:
        cmd += ["-c:v", "copy"]
    cmd += _audio_args(job, ext)

    if ext in (".mp4", ".mov", ".m4v"):
        cmd += ["-movflags", "+faststart"]
    cmd += ["-avoid_negative_ts", "make_zero", job.output_path]
    return cmd


_PROGRESS_RE = re.compile(r"time=(\d+):(\d+):(\d+(?:\.\d+)?)")
_STATS_PREFIXES = ("frame=", "size=", "video:", "audio:")
_HINTS = (
    ("Could not find tag for codec", "This container cannot hold the video's current format. "
                                    "Choose a quality preset (re-encode) or another format."),
    ("not currently supported in container", "This container cannot hold the video's current "
                                             "format. Choose a quality preset (re-encode)."),
    ("Could not write header", "This container cannot hold the video's current format. "
                               "Choose a quality preset (re-encode) or another format."),
    ("Invalid data found when processing input", "ffmpeg could not read the source "
                                                 "(the file may be damaged or not a video)."),
    ("Permission denied", "Windows would not let ffmpeg write there. Pick another folder."),
    ("No space left", "The drive is full."),
)


def summarize_ffmpeg_error(stderr_text: str) -> str:
    """Pick the useful part of ffmpeg's stderr for a user-facing message."""
    lines = [ln.strip() for ln in stderr_text.splitlines() if ln.strip()]
    lines = [ln for ln in lines
             if not ln.startswith(_STATS_PREFIXES) and "time=" not in ln
             and not ln.startswith(("ffmpeg version", "built with", "configuration:", "lib"))]
    for needle, hint in _HINTS:
        if needle in stderr_text:
            return hint
    return " | ".join(lines[-2:])[:300] if lines else "no details from ffmpeg"


def _remove_partial(path: str, source: str) -> None:
    if same_file(path, source):
        return
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError as exc:
        log.warning("could not remove partial output %s: %s", path, exc)


def _finish(job: TrimJob, on_done: Callable[[TrimJob], None] | None) -> None:
    job.done = True
    if not job.error:
        job.progress = 100.0
    if on_done:
        try:
            on_done(job)
        except Exception:
            log.exception("on_done callback failed")


def _pre_check(job: TrimJob) -> list[str] | None:
    """Validate the job and build the command. Sets job.error and returns None on failure."""
    try:
        start, end = validate_trim(job.start, job.end, job.source_duration)
        if not os.path.isfile(job.input_path):
            raise TrimError(f"Source file not found: {job.input_path}")
        if same_file(job.input_path, job.output_path):
            raise TrimError(
                "The output would overwrite the source video. Pick a different file name.")
        out_dir = os.path.dirname(os.path.abspath(job.output_path))
        if not os.path.isdir(out_dir):
            raise TrimError(f"Output folder does not exist: {out_dir}")
        job.start, job.end = start, end
        return build_trim_cmd(job)
    except TrimError as exc:
        job.error = str(exc)
    except FFmpegNotFoundError as exc:
        job.error = str(exc)
        log.error("%s", exc)
    return None


def run_trim(
    job: TrimJob,
    on_progress: Callable[[float], None] | None = None,
    on_done: Callable[[TrimJob], None] | None = None,
) -> None:
    """Run the trim in a background thread. Calls on_progress(0-100) and on_done(job).

    If the job is invalid, `on_done` runs immediately on the calling thread with
    `job.error` set. Callbacks otherwise run on worker threads: marshal to the UI
    with services.ui_bridge.
    """
    cmd = _pre_check(job)
    if cmd is None:
        _finish(job, on_done)
        return
    duration = job.end - job.start
    log.info("trim %s -> %s  [%.3f..%.3f] copy=%s", job.input_path, job.output_path,
             job.start, job.end, job.copy_streams)

    def _read_stderr(proc: subprocess.Popen, tail: collections.deque) -> None:
        assert proc.stderr is not None
        for line in proc.stderr:  # universal newlines: ffmpeg's \r progress updates split here
            line = line.rstrip()
            match = _PROGRESS_RE.search(line)
            if match:
                t = int(match.group(1)) * 3600 + int(match.group(2)) * 60 + float(match.group(3))
                job.progress = min(99.9, (t / duration) * 100)
                if on_progress:
                    try:
                        on_progress(job.progress)
                    except Exception:
                        log.exception("on_progress callback failed")
            elif line:
                tail.append(line)

    def _worker() -> None:
        tail: collections.deque[str] = collections.deque(maxlen=40)
        try:
            job.process = proc = subprocess.Popen(
                cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
                creationflags=_NO_WINDOW,
            )
            reader = threading.Thread(target=_read_stderr, args=(proc, tail), daemon=True)
            reader.start()
            while True:
                try:
                    proc.wait(timeout=0.1)
                    break
                except subprocess.TimeoutExpired:
                    if job.cancel_event.is_set():
                        proc.kill()
                        proc.wait()
                        break
            reader.join(timeout=5)

            if job.cancel_event.is_set():
                job.error = "Cancelled"
            elif proc.returncode != 0:
                job.error = f"ffmpeg failed: {summarize_ffmpeg_error(chr(10).join(tail))}"
                log.error("ffmpeg exit %s: %s", proc.returncode, "\n".join(tail))
            elif not os.path.isfile(job.output_path) or os.path.getsize(job.output_path) == 0:
                job.error = "ffmpeg finished but wrote no output file"
                log.error("no output for %s", job.output_path)
        except OSError as exc:
            job.error = f"Could not run ffmpeg: {exc}"
            log.exception("failed to launch ffmpeg")
        finally:
            if job.error:
                _remove_partial(job.output_path, job.input_path)
            _finish(job, on_done)

    threading.Thread(target=_worker, name="ffmpeg-trim", daemon=True).start()
