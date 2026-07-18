<!-- claude-backend:generated:start -->
# video_trimmer

## Overview

- **Files**: 24 (.py (19), .md (5))
- **Entry points**: `main.py`
- **Dependencies**: customtkinter, opencv-python, Pillow
- **Key files**: `CLAUDE.md`, `requirements.txt`, `.gitignore`

## Structure

```
services/  (4 files)
widgets/  (12 files)
```

## Conventions

- Use `os.path` for path operations (legacy style)
- Type hints are used extensively -- maintain them
- Prefer f-strings for string formatting
- Absolute imports preferred

## Modules

- `app.py` -- Main application window — layout, keybinds, drag-and-drop, widget wiring
- `config.py` -- App-wide constants: colors, fonts, paths, supported formats
- `main.py` -- Video Trimmer — entry point [entry]
- `services/batch_split_service.py` -- Batch split service — scan folder, compute segments, run sequential trims
- `services/edit_transforms.py` -- Preview + FFmpeg helpers for crop, rotate, flip
- `services/ffmpeg_service.py` -- FFmpeg / FFprobe wrapper — metadata extraction and video trimming
- `services/video_service.py` -- OpenCV-based video operations — frame extraction, thumbnails, playback state
- `widgets/batch_file_row.py` -- One row in the batch file list — name, duration, status badge, progress
- `widgets/batch_panel.py` -- Batch panel — top-level UI for the Batch mode
- `widgets/edit_controls.py` -- Crop / rotate / flip controls wired to VideoState
- `widgets/export_dialog.py` -- Export dialog — format/quality selection, progress bar, cancel button
- `widgets/mode_switcher.py` -- Mode switcher — segmented Single/Batch toggle at top of window
- `widgets/split_config_panel.py` -- Split configuration panel — mode radio, preset buttons, custom N, encode options
- `widgets/status_bar.py` -- Bottom status bar — shows status text, file info, and duration
- `widgets/timeline.py` -- Timeline widget — thumbnail strip with draggable trim handles and playhead
- `widgets/toast.py` -- Non-blocking toast notification — slides in from top-right, auto-dismisses
- `widgets/toolbar.py` -- Top toolbar — app branding, open file, metadata summary
- `widgets/trim_controls.py` -- Trim controls — timecode entries, set in/out buttons, trim duration display
- `widgets/video_preview.py` -- Video preview panel — displays OpenCV frames in a CTkLabel with playback controls

<!-- claude-backend:generated:end -->
