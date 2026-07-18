---
name: video_trimmer Architecture
description: Module map and dependency graph for video_trimmer
type: reference
---

# video_trimmer Architecture

## (root)/

- `app.py`: Main application window — layout, keybinds, drag-and-drop, widget wiring. | exports: VideoTrimmerApp
- `config.py`: App-wide constants: colors, fonts, paths, supported formats. | exports: APP_NAME, APP_VERSION, COLORS, FONT_UI, FONT_UI_SMALL, FONT_UI_BOLD, FONT_MONO, FONT_MONO_SMALL
- `main.py`: Video Trimmer — entry point. | exports: main

## services/

- `services/batch_split_service.py`: Batch split service — scan folder, compute segments, run sequential trims. | exports: STATUS_PENDING, STATUS_RUNNING, STATUS_DONE, STATUS_SKIPPED, STATUS_FAILED, STATUS_UNREADABLE, SplitConfig, BatchFileEntry
- `services/edit_transforms.py`: Preview + FFmpeg helpers for crop, rotate, flip. | exports: crop_box_pixels, apply_pil_transforms, ffmpeg_vf_chain, edits_active
- `services/ffmpeg_service.py`: FFmpeg / FFprobe wrapper — metadata extraction and video trimming. | exports: VideoMeta, format_time, parse_time, get_metadata, TrimJob, build_trim_cmd, run_trim
- `services/video_service.py`: OpenCV-based video operations — frame extraction, thumbnails, playback state. | exports: VideoState, open_video, read_frame_at, read_frame_at_time, generate_thumbnails, PlaybackEngine

## widgets/

- `widgets/batch_file_row.py`: One row in the batch file list — name, duration, status badge, progress. | exports: BatchFileRow
- `widgets/batch_panel.py`: Batch panel — top-level UI for the Batch mode. | exports: BatchPanel
- `widgets/edit_controls.py`: Crop / rotate / flip controls wired to VideoState. | exports: EditControls
- `widgets/export_dialog.py`: Export dialog — format/quality selection, progress bar, cancel button. | exports: ExportDialog
- `widgets/mode_switcher.py`: Mode switcher — segmented Single/Batch toggle at top of window. | exports: ModeSwitcher
- `widgets/split_config_panel.py`: Split configuration panel — mode radio, preset buttons, custom N, encode options. | exports: SplitConfigPanel
- `widgets/status_bar.py`: Bottom status bar — shows status text, file info, and duration. | exports: StatusBar
- `widgets/timeline.py`: Timeline widget — thumbnail strip with draggable trim handles and playhead. | exports: Timeline
- `widgets/toast.py`: Non-blocking toast notification — slides in from top-right, auto-dismisses. | exports: Toast
- `widgets/toolbar.py`: Top toolbar — app branding, open file, metadata summary. | exports: Toolbar
- `widgets/trim_controls.py`: Trim controls — timecode entries, set in/out buttons, trim duration display. | exports: TrimControls
- `widgets/video_preview.py`: Video preview panel — displays OpenCV frames in a CTkLabel with playback controls. | exports: VideoPreview
