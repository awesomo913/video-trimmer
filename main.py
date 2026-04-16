"""Video Trimmer — entry point."""

import sys
import os

# Ensure package imports work when run as `python main.py`
sys.path.insert(0, os.path.dirname(__file__))

from app import VideoTrimmerApp  # noqa: E402


def main():
    app = VideoTrimmerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
