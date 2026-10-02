"""Build VideoTrimmer.exe, a standalone Windows executable.

Run it with the interpreter of a clean venv so the bundle does not pull in
unrelated packages:

    .venv\\Scripts\\python.exe build.py

Output: dist\\VideoTrimmer.exe (CI picks it up from dist\\ for releases).

ffmpeg is NOT expected on the build or user machine: the binary shipped by the
`imageio-ffmpeg` wheel is collected into the exe (`--collect-data`), and
services/ffmpeg_locator.py finds it again at run time. See THIRD_PARTY.md for
that binary's license.
"""
from __future__ import annotations

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP_NAME = "VideoTrimmer"
MAIN = os.path.join(HERE, "main.py")
ICON = os.path.join(HERE, "assets", "videotrimmer.ico")

_COLLECT_DATA = [
    # customtkinter's theme JSON assets are not picked up by default.
    "customtkinter",
    # The real ffmpeg.exe lives in imageio_ffmpeg/binaries/ as package data.
    "imageio_ffmpeg",
    # The native tkdnd Tcl extension; without it OS drag-and-drop silently fails.
    "tkinterdnd2",
]

_COLLECT_SUBMODULES = ["tkinterdnd2"]


def build_exe() -> None:
    args = [
        sys.executable, "-m", "PyInstaller",
        "--clean", "--noconfirm",
        "--onefile", "--windowed",
        f"--name={APP_NAME}",
    ]
    if os.path.isfile(ICON):
        args.append(f"--icon={ICON}")
    for pkg in _COLLECT_DATA:
        args.append(f"--collect-data={pkg}")
    for pkg in _COLLECT_SUBMODULES:
        args.append(f"--collect-submodules={pkg}")
    args.append(MAIN)

    print("[build] Running PyInstaller (this can take a few minutes)...")
    # Timeout so a hung PyInstaller fails loudly; 20 minutes covers cold caches.
    subprocess.check_call(args, cwd=HERE, timeout=1200)
    print("[build] PyInstaller complete.")


def main() -> None:
    build_exe()
    exe_path = os.path.join(HERE, "dist", f"{APP_NAME}.exe")
    if not os.path.isfile(exe_path):
        raise SystemExit(f"[build] FAILED: expected {exe_path} but it does not exist")
    size_mb = round(os.path.getsize(exe_path) / (1024 * 1024), 1)
    print(f"[build] OK -> {exe_path}  ({size_mb} MB)")


if __name__ == "__main__":
    main()
