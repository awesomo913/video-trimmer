# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - Unreleased

First release with an automated build, tests and documentation.

### Added

- ffmpeg is bundled (through the `imageio-ffmpeg` package): nothing to install, no `PATH` setup.
- A log file at `%LOCALAPPDATA%\VideoTrimmer\logs\app.log`.
- 125 automated tests, CI (ruff + pytest) and a tag-triggered release build with `SHA256SUMS.txt`.

### Changed

- Video details are read from ffmpeg itself, so `ffprobe` is no longer needed.
- Batch split never overwrites earlier results; a re-run saves `name (2).mp4` and so on.
- Preview audio needs `ffplay` on `PATH`; without it the preview is silent (exports are unaffected).

### Fixed

- Exporting to WebM failed with H.264/AAC streams; WebM now uses VP9 + Opus.
- File names with accents, CJK characters or spaces could break progress reading.
- A failed export now shows what ffmpeg said (with a plain-language hint for common cases) instead of "exit code 1".
- Cancelled or failed exports leave no half-written file behind.
- In = out, a start past the end of the video, or an end beyond the end are handled with clear messages (an end beyond the video is clamped).
- Exporting can never overwrite the source video, including through paths spelled differently.
- Phone videos with a rotation flag show the right resolution.
- Videos with subtitle or data tracks (common in `.ts` files) no longer fail stream copy.
- A tiny leftover chunk in duration-split mode no longer fails the whole file.
- Batch: a failed file is reported by name with the failing part, and the rest continue.
- Dropping a file while in Batch mode now updates the mode switch.
- Thumbnails of a previously opened video no longer appear after loading another.
- Background threads no longer touch the window directly; results are handed to the UI thread.

## [1.2.0] - 2026-04-21

- Batch split mode: split every video in a folder into equal parts or fixed-length chunks.

## [1.0.0] - 2026-04-15

- Open, preview, trim and export videos with a thumbnail timeline.
