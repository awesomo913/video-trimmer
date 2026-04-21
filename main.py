"""Video Trimmer — entry point."""

import sys
import os
from pathlib import Path

# Ensure package imports work when run as `python main.py`
sys.path.insert(0, os.path.dirname(__file__))

# Install shared crash logger (per workspace Crash Log Rule)
_SCRIPTS = Path.home() / ".claude" / "scripts"
if _SCRIPTS.exists():
    sys.path.insert(0, str(_SCRIPTS))
    try:
        from crash_logger import install, log_event  # noqa: E402
        install(project_root=Path(__file__).parent)
    except Exception:
        def log_event(*_a, **_kw):  # no-op fallback
            pass
else:
    def log_event(*_a, **_kw):
        pass

from app import VideoTrimmerApp  # noqa: E402


def main():
    log_event("info", "session_start", {"app": "video_trimmer"})
    app = VideoTrimmerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
