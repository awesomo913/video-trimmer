# Video Trimmer — Tutorial
**Last updated:** 2026-04-15 (v1.0.0)

---

## 1. Quickstart

Open a video, drag the green/red handles to pick your clip, hit Ctrl+E to export.

**Install:**
```bash
uv pip install -r requirements.txt
```

**Run:**
```bash
python main.py
```

**What you should see:** A dark window titled "Video Trimmer v1.0.0" with a black preview area and an empty timeline strip at the bottom. Top-right shows "No file loaded."

**What now?** Press `Ctrl+O` to open a video, then read Feature Walkthrough below.

---

## 2. Feature Walkthrough

### Open a video
- **What it does:** Loads any common video into the player.
- **When to use it:** First thing you do.
- **How:** Click `Open` in the toolbar, or press `Ctrl+O`. Pick a file.
- **Example:** Open a `.mp4` from your phone → preview shows frame 1, timeline fills with ~24 thumbnail previews, toolbar shows resolution/codec/duration/size.
- **Gotchas:** Very long videos (>1 hour) may take a few seconds to generate thumbnails. The status bar shows "Loading..." in yellow while it works.

### Play / pause / seek
- **What it does:** Watch the video in the preview area.
- **How:**
  - `Space` — play/pause
  - Click anywhere on the timeline — seek to that position
  - `Left` / `Right` arrow — step 1 frame back/forward
  - `Shift + Left` / `Shift + Right` — jump 5 seconds
  - Speed dropdown (bottom-right of preview): 0.25x to 2.0x
- **Example:** Press Space to play, hit `Right` three times to scrub 3 frames forward, hit Space again to pause.
- **Gotchas:** Playback loops from trim end back to trim start, so if you set trim points the preview auto-loops your clip.

### Set trim points
- **What it does:** Pick the start (IN) and end (OUT) of your exported clip.
- **When to use it:** Every time — the whole point of the app.
- **How (three ways):**
  1. **Keyboard:** Play to the moment you want, press `[` for start, `]` for end.
  2. **Drag the handles:** Grab the green handle (left edge) or red handle (right edge) on the timeline and drag.
  3. **Type timecodes:** Click the IN or OUT field, type `1:23.45`, press Enter.
- **Example:** A 30-second clip from a 2-hour video: seek to 00:45, press `[`; seek to 01:15, press `]`. "Trim Duration" shows 00:30.00 in pink.
- **Gotchas:**
  - The IN point can't pass the OUT point (and vice versa) — they're clamped at 0.1s apart.
  - The `Reset` button restores trim to the full video length.

### Export
- **What it does:** Writes your trimmed clip as a new file.
- **How:** Press `Ctrl+E` or click `Export` in the toolbar. A dialog appears:
  - **Output Format:** MP4, MKV, AVI, WebM, MOV
  - **Quality Preset:**
    - `Copy (fastest, lossless)` — instant, no quality loss, keeps original codec. Use this unless you need to change format or compress.
    - `High (CRF 18)` — re-encodes at near-visually-lossless quality.
    - `Medium (CRF 23)` — balanced.
    - `Low (CRF 28)` — smaller file, noticeable quality loss.
    - `Compact (CRF 35)` — tiny file, visible compression.
  - **Include audio** — uncheck to strip audio.
- Click `Export`, pick a save location. Progress bar fills as ffmpeg works. When it hits 100%, the dialog auto-closes and a green "Exported: ..." toast appears.
- **Gotchas:**
  - `Copy` mode only works when the output container matches or is compatible with the source codec. If ffmpeg refuses, pick a quality preset instead (it re-encodes).
  - `Cancel` during export kills the ffmpeg process and deletes the partial file.

---

## 3. Common Workflows / Recipes

### Recipe: Extract a 30-second highlight from a 1-hour recording
1. `Ctrl+O`, pick the recording.
2. Click on the timeline near the timestamp you want (or press Space to start playing and use arrows to find it).
3. Press `[` to mark IN.
4. Seek to the end of your highlight, press `]` to mark OUT.
5. `Ctrl+E`, pick `MP4` + `Copy (fastest, lossless)`, click Export.
6. **Result:** A 30-second MP4 next to your source, no quality loss, done in ~1 second.

### Recipe: Convert a big MKV to a compressed MP4
1. `Ctrl+O`, pick the MKV.
2. Don't change trim points — leave the full video selected.
3. `Ctrl+E`, pick `MP4` + `Low (CRF 28)`, click Export.
4. **Result:** A much smaller MP4. Takes longer (real-time encoding) but fine for sharing.

### Recipe: Strip audio from a video
1. Open file, set trim points if needed.
2. `Ctrl+E`, uncheck `Include audio`, click Export.
3. **Result:** Same video, no audio track.

---

## 4. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Window opens then closes immediately | Missing Python dep | `uv pip install -r requirements.txt` |
| "Failed to open: ..." toast | Corrupt/unsupported file | Try a different file, or check `ffprobe file.mp4` manually |
| Preview is black, no frames | Unusual codec OpenCV can't decode | File will still export fine via ffmpeg — the preview is just blind to it |
| Export fails with "codec not found" | Picked `Copy` with an incompatible container | Switch quality to `Medium (CRF 23)` — it'll re-encode |
| Thumbnails don't appear | Still generating (background thread) | Wait 1-2 seconds |
| App won't start, `ModuleNotFoundError` | CustomTkinter not installed | `uv pip install customtkinter opencv-python pillow` |
| ffmpeg not found error | Bundled path broken | Check `C:\Users\computer\Desktop\AI\ffmpeg\ffmpeg-8.1-essentials_build\bin\` exists, or install ffmpeg to system PATH |

---

## 5. FAQ

- **Q: Can I trim audio-only files (MP3)?** A: No, this is video-only. Use Audacity for audio.
- **Q: Does it modify my original file?** A: No, never. Exports always write a new file.
- **Q: Can I cut OUT a section (keep the beginning and end, drop the middle)?** A: Not in v1.0.0. Only single-region trim. Planned for a future version.
- **Q: Why is `Copy` mode sometimes slightly off on the cut point?** A: Stream copy can only cut at keyframes. If frame-accurate matters, use a quality preset (re-encodes).
- **Q: Does it upload my video anywhere?** A: No. Everything runs locally via ffmpeg on your machine.
- **Q: Can I drag-and-drop a file onto the window?** A: Not yet — the stub is there but needs `tkinterdnd2` installed.

---

## 6. Changelog

### 2026-04-15 — v1.0.0 (initial release)
- Added: Open any common video format (MP4, MKV, MOV, WebM, AVI, FLV, WMV, TS, M4V, MPG, 3GP, and more)
- Added: Video preview with play/pause/seek/frame-step/speed controls
- Added: Visual timeline with thumbnail strip and draggable in/out handles
- Added: Trim controls with typed timecode entries and Set IN/OUT buttons
- Added: Export dialog with 5 output formats, 5 quality presets, audio toggle
- Added: Stream-copy mode for instant lossless trim when format unchanged
- Added: Progress bar during export with cancel support
- Added: Keyboard shortcuts: Space, arrows, Shift+arrows, `[`, `]`, Ctrl+O, Ctrl+E
- Added: Toast notifications for success/error/info feedback
- Added: Crash logger integration writes to `logs/crash_*.log` on uncaught errors
