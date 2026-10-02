"""File logging. A windowed exe has no stderr, so without this every log line is lost."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

APP_DIR_NAME = "VideoTrimmer"

_logger = logging.getLogger(__name__)
_configured = False


def log_file_path() -> Path:
    """Where the log lives (Windows: %LOCALAPPDATA%/VideoTrimmer/logs/app.log)."""
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".local" / "state")
    return Path(base) / APP_DIR_NAME / "logs" / "app.log"


def setup_logging() -> Path | None:
    """Log to a file always, and to stderr when there is one.

    Returns the log path, or None if the file could not be opened (logging then
    falls back to stderr only). Safe to call more than once.
    """
    global _configured
    path = log_file_path()
    if _configured:
        return path
    _configured = True

    fmt = logging.Formatter("%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
                            "%Y-%m-%d %H:%M:%S")
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if sys.stderr is not None:
        stream = logging.StreamHandler()
        stream.setFormatter(fmt)
        root.addHandler(stream)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(path, encoding="utf-8")
    except OSError as exc:
        _logger.warning("Could not open log file %s: %s", path, exc)
        return None
    handler.setFormatter(fmt)
    root.addHandler(handler)
    return path


def install_excepthooks() -> None:
    """Send uncaught exceptions (main thread and worker threads) to the log."""
    import threading

    def _hook(exc_type, exc, tb):
        _logger.critical("Uncaught exception", exc_info=(exc_type, exc, tb))

    def _thread_hook(args):
        _logger.critical(
            "Uncaught exception in thread %s",
            getattr(args.thread, "name", "?"),
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )

    sys.excepthook = _hook
    threading.excepthook = _thread_hook
