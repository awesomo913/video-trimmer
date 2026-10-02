"""Video Trimmer — entry point."""

import logging
import os
import sys

# Ensure package imports work when run as `python main.py`
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.applog import install_excepthooks, setup_logging  # noqa: E402

log = logging.getLogger("video_trimmer")


def main() -> None:
    log_path = setup_logging()
    install_excepthooks()
    log.info("session start (log: %s)", log_path)

    # Imported after logging is set up so import-time problems are recorded too.
    from app import VideoTrimmerApp

    app = VideoTrimmerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
