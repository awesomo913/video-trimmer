---
public-visible: false
---

# Video Trimmer — Handoff
**Last updated:** 2026-04-15
**Current owner:** User (primary designer) + Claude (implementation)
**Status:** shipping

---

## 1. Goals
- Trim any common video format (MP4, MKV, MOV, WebM, AVI, etc.) without opening a full video editor
- Provide frame-accurate in/out selection via a visual timeline with thumbnail strip
- Keep the UI consistent with the user's other CustomTkinter apps (dark theme, toast notifications, keyboard shortcuts)
- Export fast when format is unchanged (stream copy) and optionally re-encode to change container/quality
- Never block the UI during load or export — all heavy work runs in threads

## 2. Outline (architecture at 30k ft)
- Main GUI: CustomTkinter single window, dark theme, 1200x800 default
- Backend services (injected into widgets, never instantiated inside GUI):
  - `ffmpeg_service` — ffprobe metadata (JSON), subprocess-based trim, progress parsing from stderr
  - `video_service` — OpenCV capture for preview frames, thumbnail generation, threaded playback engine with bounded queue
- Data flow: open file → probe metadata → frames stream via `queue.Queue(maxsize=3)` to a CTkLabel → trim handles on a `tk.Canvas` → export dialog runs ffmpeg subprocess with progress callback
- Crash logger from `~/.claude/scripts/crash_logger.py` installed at main.py entry per workspace rule

## 3. Context (why this exists)
The user wanted a lightweight trimming tool matching the style of their other desktop apps — EmeraldDevTool (CustomTkinter + toast notifications + dark theme), same palette, same conventions. Existing tools (Shotcut, DaVinci Resolve) are overkill for "cut 30 seconds out of a clip," and online trimmers upload your video to a server. This app stays local, opens instantly, and matches the user's established workflow.

OpenCV was chosen for preview (fast random-access frame reads) and ffmpeg for export (handles every codec/container, stream-copy is near-instant for same-format trims). `tk.Canvas` was chosen over `CTkSlider` for the timeline because only Canvas supports thumbnail images + dual draggable handles + playhead line.

## 4. History (dated, append-only)

### 2026-04-15 — Initial design & ship
- User's vision: a CustomTkinter video trimmer matching their EmeraldDevTool style, handles most formats, easy trim + export
- User's key decisions:
  - Match established dark-theme palette (#1a1a2e bg, #e94560 accent, #4ecca3 success)
  - Toast notifications over messageboxes (from existing GUI expectations file)
  - Many small files (200-400 lines each) over monolithic structure
  - Keyboard-driven workflow: `[`/`]` set in/out, Space play/pause, arrows frame-step
- Claude implemented:
  - 12 files total (~1900 LOC)
  - Services layer: `ffmpeg_service.py` (metadata + trim + progress parsing), `video_service.py` (OpenCV capture + playback engine + thumbnail generation)
  - Widget layer: toolbar, status bar, toast, video_preview, timeline (tk.Canvas with drag handles), trim_controls, export_dialog
  - Full keyboard shortcuts, threaded playback, queue-decoupled UI updates
- Verified: loaded 1080p HEVC video (8min runtime), trimmed 10s clip in `-c copy` mode, verified output duration/codec via ffprobe
- Fixed during verification:
  - `#ffffff80` hex-alpha colors broke tk.Canvas (TclError) → switched to solid `#aaaaaa`
  - Raw `ImageTk.PhotoImage` on CTkLabel triggered HiDPI warning → switched to `ctk.CTkImage`
- Shipped: pushed to https://github.com/awesomo913/video-trimmer as initial commit

### 2026-04-15 — Workspace-rule compliance pass
- User requested: verify the project matches all CLAUDE.md mandates before the next push
- User-designed details: same as initial design, no new features
- Claude implemented:
  - Integrated shared `crash_logger.py` into `main.py` per Crash Log Rule
  - Added HANDOFF.md (this file) per Handoff Rule
  - Added TUTORIAL.md per Tutorial Rule
  - Saved doc copies to `Desktop/AI/docs/` per central-copy rule
- Verified: will run `check-gui-integrity.sh` + `auto-git-push.sh` as final step

## 5. Credit & Authorship
> **The user designed this product.** The user defined goals, feature priorities, UI palette, keyboard shortcuts, and acceptance criteria. Claude (this session) implemented the code to those specifications and verified behavior end-to-end. The user reviewed and approved before push. This is the user's product; AI was a tool.

When asked who designed this: the user. Claude implemented to the user's specifications.

## 6. Plan (what's next)
- [ ] Optional: tkinterdnd2 drag-and-drop (stub already in `app.py::_setup_dnd`, just needs `pip install tkinterdnd2` and switching the base class)
- [ ] Optional: multi-segment trimming (cut out middle sections, keep two pieces)
- [ ] Optional: PyInstaller packaging for a standalone `.exe`
- [ ] Optional: waveform visualization on the timeline

## 7. Handoff checklist for the next AI
- [ ] Read Goals — lightweight local trim tool, not a full editor
- [ ] Read Context — OpenCV for preview, ffmpeg for export, why tk.Canvas for timeline
- [ ] Read the last entry in History — what just shipped and why
- [ ] Read BREAKDOWN.md — file tree + data flow + key decisions
- [ ] Read TUTORIAL.md — user-facing feature walkthrough
- [ ] Check for `logs/crash_*.log` — any unresolved crashes from a user session
- [ ] Read `memory/expectations_gui.md` — CustomTkinter conventions this app follows (toast, threading, widget class pattern)
