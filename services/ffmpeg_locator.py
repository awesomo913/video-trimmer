"""Find the ffmpeg (and optional ffplay) binaries.

Nobody has to install anything: the `imageio-ffmpeg` wheel ships a real ffmpeg
binary, and the PyInstaller build collects it into the exe. A system ffmpeg on
PATH is only a fallback. `ffprobe` is never needed (metadata is read from
`ffmpeg -i`), and `ffplay` is optional (it only provides audio in the preview).
"""

from __future__ import annotations

import logging
import os
import shutil
from functools import lru_cache

log = logging.getLogger(__name__)


class FFmpegNotFoundError(RuntimeError):
    """No usable ffmpeg binary could be located."""


@lru_cache(maxsize=1)
def find_ffmpeg() -> str:
    """Return the path to an ffmpeg executable, or raise FFmpegNotFoundError."""
    problems: list[str] = []
    try:
        import imageio_ffmpeg

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.isfile(exe):
            return exe
        problems.append(f"imageio-ffmpeg reported {exe!r}, which does not exist")
    except (ImportError, RuntimeError) as exc:
        problems.append(f"imageio-ffmpeg unavailable: {exc}")

    system = shutil.which("ffmpeg")
    if system:
        log.info("using system ffmpeg at %s (%s)", system, "; ".join(problems))
        return system
    raise FFmpegNotFoundError(
        "ffmpeg was not found. Reinstall Video Trimmer, or install ffmpeg and put it on PATH. "
        + "; ".join(problems)
    )


@lru_cache(maxsize=1)
def find_ffplay() -> str | None:
    """Return ffplay if one is installed (used only for preview audio), else None."""
    found = shutil.which("ffplay")
    if found:
        return found
    try:
        sibling = os.path.join(os.path.dirname(find_ffmpeg()), "ffplay.exe")
    except FFmpegNotFoundError:
        return None
    return sibling if os.path.isfile(sibling) else None
