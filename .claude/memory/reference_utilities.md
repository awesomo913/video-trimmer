---
name: video_trimmer Utilities
description: Reusable functions and their locations in video_trimmer
type: reference
---

# Reusable Functions in video_trimmer

| Function | Module | Purpose |
|----------|--------|---------|
| `VideoTrimmerApp` | `app.py` | Root application window. |
| `APP_NAME` | `config.py` | -- |
| `APP_VERSION` | `config.py` | -- |
| `COLORS` | `config.py` | -- |
| `FONT_UI` | `config.py` | -- |
| `FONT_UI_SMALL` | `config.py` | -- |
| `FONT_UI_BOLD` | `config.py` | -- |
| `FONT_MONO` | `config.py` | -- |
| `FONT_MONO_SMALL` | `config.py` | -- |
| `FONT_TITLE` | `config.py` | -- |
| `FFMPEG_BIN` | `config.py` | -- |
| `main` | `main.py` | -- |
| `STATUS_PENDING` | `services/batch_split_service.py` | -- |
| `STATUS_RUNNING` | `services/batch_split_service.py` | -- |
| `STATUS_DONE` | `services/batch_split_service.py` | -- |
| `STATUS_SKIPPED` | `services/batch_split_service.py` | -- |
| `STATUS_FAILED` | `services/batch_split_service.py` | -- |
| `STATUS_UNREADABLE` | `services/batch_split_service.py` | -- |
| `SplitConfig` | `services/batch_split_service.py` | Per-batch configuration: how to split and how to encode. |
| `BatchFileEntry` | `services/batch_split_service.py` | One video in the batch — populated by scan, mutated by runner. |
| `BatchSplitJob` | `services/batch_split_service.py` | Top-level batch run state. |
| `ScanError` | `services/batch_split_service.py` | Raised when the folder itself cannot be read (permissions, missing, etc.). |
| `crop_box_pixels` | `services/edit_transforms.py` | Return (x, y, w, h) in source pixel coords, or None if crop disabled. |
| `apply_pil_transforms` | `services/edit_transforms.py` | Apply crop / rotation / flip for preview and snapshot export. |
| `ffmpeg_vf_chain` | `services/edit_transforms.py` | Build -vf filter string, or None when no video transforms. |
| `edits_active` | `services/edit_transforms.py` | -- |
| `VideoMeta` | `services/ffmpeg_service.py` | -- |
| `format_time` | `services/ffmpeg_service.py` | -- |
| `parse_time` | `services/ffmpeg_service.py` | -- |
| `get_metadata` | `services/ffmpeg_service.py` | Run ffprobe and return structured metadata. |
| `TrimJob` | `services/ffmpeg_service.py` | Holds state for a running trim operation. |
| `build_trim_cmd` | `services/ffmpeg_service.py` | Build the ffmpeg command list for a trim job. |
| `run_trim` | `services/ffmpeg_service.py` | Run the trim in a background thread. Calls on_progress(0-100) and on_done(job). |
| `VideoState` | `services/video_service.py` | Shared mutable state for the currently loaded video. |
| `open_video` | `services/video_service.py` | Open a video file and return populated VideoState. |
| `read_frame_at` | `services/video_service.py` | Seek to a specific frame and return it as a PIL Image. |
| `read_frame_at_time` | `services/video_service.py` | Seek to a specific time and return the frame. |
| `generate_thumbnails` | `services/video_service.py` | Generate evenly-spaced thumbnail images in a background thread. |
| `PlaybackEngine` | `services/video_service.py` | Threaded playback engine — pushes frames to a queue for the UI to consume. |
| `BatchFileRow` | `widgets/batch_file_row.py` | One row: filename, duration, status badge, thin progress bar. |
| `BatchPanel` | `widgets/batch_panel.py` | Self-contained widget swapped into the main window in Batch mode. |
| `EditControls` | `widgets/edit_controls.py` | Transforms applied to preview and to exported video. |
| `ExportDialog` | `widgets/export_dialog.py` | Modal dialog for configuring and running a video export. |
| `ModeSwitcher` | `widgets/mode_switcher.py` | Two-button segmented control. Active button gets accent color. |
| `SplitConfigPanel` | `widgets/split_config_panel.py` | Compact panel exposing all split settings as a SplitConfig. |
| `StatusBar` | `widgets/status_bar.py` | Bottom bar with left status text and right-aligned file info. |
| `Timeline` | `widgets/timeline.py` | Canvas-based timeline with thumbnail strip, trim handles, and playhead. |
| `Toast` | `widgets/toast.py` | Ephemeral toast that appears top-right and auto-dismisses. |
| `Toolbar` | `widgets/toolbar.py` | Horizontal toolbar with branding, buttons, and metadata display. |
| `TrimControls` | `widgets/trim_controls.py` | Horizontal bar with in/out timecodes, set buttons, and trim duration. |
| `VideoPreview` | `widgets/video_preview.py` | Displays the current video frame, scaled to fit the available space. |
