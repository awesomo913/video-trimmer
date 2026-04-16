# Video Trimmer — Breakdown
**Created:** 2026-04-15
**Location:** C:\Users\computer\Desktop\AI\video_trimmer\
**Language/Stack:** Python 3.11 + CustomTkinter + OpenCV + FFmpeg

---

## 1. What It Does
A desktop video trimmer that opens virtually any video format, shows a preview with playback controls, and lets you set precise in/out trim points via a visual timeline with thumbnail strip and draggable handles. Exports trimmed clips using FFmpeg with format/quality options and real-time progress.

## 2. How To Run It
- **Install:** `uv pip install -r requirements.txt`
- **Requires:** FFmpeg 8.1 (already at `Desktop/AI/ffmpeg/`), Python 3.11
- **Run:** `python main.py`
- **Basic usage:** Click Open (or Ctrl+O), pick a video, use `[` and `]` keys to set trim points, then Ctrl+E to export

## 3. Architecture & File Structure
```
video_trimmer/
├── main.py              # Entry point
├── app.py               # CTk main window, layout, keybinds
├── config.py            # Colors, fonts, ffmpeg paths, constants
├── widgets/
│   ├── toolbar.py       # Top bar: branding, open/export buttons, metadata
│   ├── status_bar.py    # Bottom bar: status + file info
│   ├── toast.py         # Slide-in toast notifications
│   ├── video_preview.py # OpenCV frame display + play/pause/seek/speed
│   ├── timeline.py      # tk.Canvas thumbnail strip, trim handles, playhead
│   ├── trim_controls.py # Timecode entries, set in/out, duration display
│   └── export_dialog.py # Format/quality picker, progress bar, cancel
├── services/
│   ├── ffmpeg_service.py # ffprobe metadata, ffmpeg trim subprocess, progress parsing
│   └── video_service.py  # OpenCV probe, frame extraction, thumbnail gen, playback engine
├── requirements.txt
└── BREAKDOWN.md
```

**Data flow:** Open file → ffprobe gets metadata + OpenCV opens capture → preview plays frames via queue → timeline generates thumbnails → user drags handles or presses `[`/`]` → export dialog spawns ffmpeg subprocess → progress parsed from stderr.

## 4. Key Decisions & Why
- OpenCV for preview, FFmpeg for export — OpenCV gives fast random-access frame reads; FFmpeg handles all codecs/containers for actual trimming
- tk.Canvas for timeline — only widget that supports thumbnails + dual draggable handles + playhead line; manually styled dark
- Frame queue (maxsize=3) decouples read thread from UI — prevents freezes, drops frames gracefully
- `-c copy` as default export — lossless and near-instant when no format change needed
- ffprobe JSON for metadata — authoritative codec/bitrate info that OpenCV doesn't expose

## 5. Development Log

### 2026-04-15 — Initial creation
- Built complete video trimmer with 12 files
- Features: open any format, preview with play/pause/seek/speed, visual timeline with thumbnails and drag handles, frame-accurate trim, export with format/quality options, progress + cancel
- Keyboard shortcuts: Space (play), arrows (frame step), Shift+arrows (5s jump), [ ] (set in/out), Ctrl+O/E (open/export)
- Dark theme matching user's established palette (#1a1a2e bg, #e94560 accent)
