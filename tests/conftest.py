"""Shared fixtures. Nothing here opens a window or touches the network.

Clips are generated with the bundled ffmpeg (lavfi test sources), so the tests
need no media files and no system ffmpeg.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.ffmpeg_locator import find_ffmpeg  # noqa: E402
from services.ffmpeg_service import TrimJob, run_trim  # noqa: E402

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def make_clip(path: Path, seconds: float = 2.0, audio: bool = True, vfr: bool = False,
              fps: int = 25, gop: int = 10) -> Path:
    """Write a tiny H.264 clip (160x120) with a keyframe every `gop` frames."""
    cmd = [find_ffmpeg(), "-hide_banner", "-loglevel", "error", "-y",
           "-f", "lavfi", "-i", f"testsrc=duration={seconds}:size=160x120:rate={fps}"]
    if audio:
        cmd += ["-f", "lavfi", "-i", f"sine=duration={seconds}"]
    if vfr:
        # Drop 2 of every 5 frames: irregular timestamps like phone footage.
        cmd += ["-vf", "select='lt(mod(n\\,5)\\,3)'", "-fps_mode", "vfr"]
    cmd += ["-c:v", "libx264", "-g", str(gop), "-pix_fmt", "yuv420p"]
    cmd += ["-c:a", "aac"] if audio else ["-an"]
    cmd.append(str(path))
    subprocess.run(cmd, check=True, capture_output=True, stdin=subprocess.DEVNULL,
                   creationflags=NO_WINDOW)
    return path


@pytest.fixture(scope="session")
def clip(tmp_path_factory) -> Path:
    return make_clip(tmp_path_factory.mktemp("clips") / "sample.mp4")


@pytest.fixture(scope="session")
def silent_clip(tmp_path_factory) -> Path:
    return make_clip(tmp_path_factory.mktemp("clips") / "silent.mp4", audio=False)


@pytest.fixture(scope="session")
def vfr_clip(tmp_path_factory) -> Path:
    return make_clip(tmp_path_factory.mktemp("clips") / "vfr.mp4", seconds=3.0, fps=30, vfr=True)


@pytest.fixture(scope="session")
def odd_name_clip(tmp_path_factory) -> Path:
    folder = tmp_path_factory.mktemp("clips") / "my videos é中"
    folder.mkdir()
    return make_clip(folder / "café clip – 1.mp4")


def run_and_wait(job: TrimJob, timeout: float = 60.0) -> list[float]:
    """Run a trim job to completion; return the progress values it reported."""
    seen: list[float] = []
    finished = threading.Event()
    run_trim(job, on_progress=seen.append, on_done=lambda _j: finished.set())
    assert finished.wait(timeout), "trim did not finish"
    return seen


def file_exists(path: os.PathLike | str) -> bool:
    return os.path.isfile(path) and os.path.getsize(path) > 0
