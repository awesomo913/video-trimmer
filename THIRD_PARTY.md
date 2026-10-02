# Third-party software

Video Trimmer's own code is MIT licensed (see `LICENSE`). The Windows release also contains:

## FFmpeg (bundled through `imageio-ffmpeg`)

- Used for every export and to read video details. It runs as a separate program (`subprocess`); it is
  not linked into the Python code.
- `imageio-ffmpeg==0.6.0` (BSD-2-Clause) ships the Windows build `ffmpeg 7.1-essentials_build-www.gyan.dev`.
  That build's configuration includes `--enable-gpl --enable-version3` (libx264, libx265 and others), so
  the **ffmpeg binary itself is GPLv3**.
- Source: <https://ffmpeg.org/download.html> and the build scripts at <https://github.com/GyanD/codexffmpeg>.
- Why it is fine to ship alongside MIT code: the program is only started as a separate executable.
  If you redistribute the release exe you take on GPL obligations for the ffmpeg binary inside it
  (for example, passing on the source offer above).

## Python packages

| Package | License |
|---|---|
| customtkinter | MIT |
| opencv-python (bundles an LGPL FFmpeg build for decoding previews) | Apache-2.0 / LGPL |
| numpy | BSD-3-Clause |
| Pillow | HPND |
| tkinterdnd2 (and the tkdnd library) | MIT |
| imageio-ffmpeg | BSD-2-Clause |

Build tools (not shipped): PyInstaller (GPL-2.0 with a bootloader exception that allows any license
for the built program), pytest, ruff.
