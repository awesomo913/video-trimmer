"""Main application window — layout, keybinds, drag-and-drop, widget wiring."""

from __future__ import annotations

import os
import sys
from tkinter import filedialog

import customtkinter as ctk

from config import (
    APP_NAME, APP_VERSION, COLORS, VIDEO_EXTENSIONS,
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_MIN_W, WINDOW_MIN_H,
)
from services.ffmpeg_service import get_metadata, format_time
from services.video_service import VideoState, open_video

from widgets.toolbar import Toolbar
from widgets.status_bar import StatusBar
from widgets.toast import Toast
from widgets.video_preview import VideoPreview
from widgets.timeline import Timeline
from widgets.trim_controls import TrimControls
from widgets.export_dialog import ExportDialog


class VideoTrimmerApp(ctk.CTk):
    """Root application window."""

    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(WINDOW_MIN_W, WINDOW_MIN_H)
        self.configure(fg_color=COLORS["bg"])

        # Try to set HiDPI awareness on Windows
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        # ── State ────────────────────────────────────────────────
        self._state = VideoState()

        # ── Layout ───────────────────────────────────────────────
        self._build_ui()
        self._bind_keys()

        # ── Drag and drop (via TkDnD if available) ───────────────
        self._setup_dnd()

    def _build_ui(self):
        # Toolbar
        self._toolbar = Toolbar(
            self, on_open=self._open_file, on_export=self._open_export,
        )
        self._toolbar.pack(fill="x", side="top")

        # Status bar
        self._status = StatusBar(self)
        self._status.pack(fill="x", side="bottom")

        # Trim controls
        self._trim_ctrl = TrimControls(
            self, state=self._state,
            on_set_in=self._set_trim_in,
            on_set_out=self._set_trim_out,
            on_trim_change=self._on_trim_change,
        )
        self._trim_ctrl.pack(fill="x", side="bottom")

        # Timeline
        self._timeline = Timeline(
            self, state=self._state,
            on_seek=self._on_timeline_seek,
            on_trim_change=self._on_trim_change,
        )
        self._timeline.pack(fill="x", side="bottom", ipady=4)

        # Video preview (takes remaining space)
        self._preview = VideoPreview(
            self, state=self._state,
            on_frame_update=self._on_frame_update,
        )
        self._preview.pack(fill="both", expand=True, side="top")

    def _bind_keys(self):
        self.bind("<Control-o>", lambda e: self._open_file())
        self.bind("<Control-O>", lambda e: self._open_file())
        self.bind("<Control-e>", lambda e: self._open_export())
        self.bind("<Control-E>", lambda e: self._open_export())
        self.bind("<space>", lambda e: self._toggle_play())
        self.bind("<Left>", lambda e: self._step_frames(-1))
        self.bind("<Right>", lambda e: self._step_frames(1))
        self.bind("<Shift-Left>", lambda e: self._jump_seconds(-5))
        self.bind("<Shift-Right>", lambda e: self._jump_seconds(5))
        self.bind("<bracketleft>", lambda e: self._set_trim_in())
        self.bind("<bracketright>", lambda e: self._set_trim_out())

    def _setup_dnd(self):
        """Enable drag-and-drop via tkinterdnd2 if available, otherwise skip."""
        try:
            self.drop_target_register("DND_Files")
            self.dnd_bind("<<Drop>>", self._on_drop)
        except Exception:
            pass

    def _on_drop(self, event):
        path = event.data.strip().strip("{}")
        if os.path.isfile(path):
            ext = os.path.splitext(path)[1].lower()
            if ext in VIDEO_EXTENSIONS:
                self._load_video(path)

    # ── File operations ──────────────────────────────────────────

    def _open_file(self):
        exts = " ".join(f"*{e}" for e in VIDEO_EXTENSIONS)
        path = filedialog.askopenfilename(
            title="Open Video File",
            filetypes=[("Video Files", exts), ("All Files", "*.*")],
        )
        if path:
            self._load_video(path)

    def _load_video(self, path: str):
        self._status.set_status("Loading...", COLORS["warning"])

        # Release previous
        self._preview.stop()
        self._state.release()

        try:
            self._state = open_video(path)
            meta = get_metadata(path)
        except Exception as exc:
            Toast(self, f"Failed to open: {exc}", "error")
            self._status.set_status("Ready")
            return

        # Wire up the new state
        self._preview.attach_state(self._state)
        self._timeline.attach_state(self._state)
        self._trim_ctrl._state = self._state
        self._trim_ctrl.update_display()

        # Update toolbar metadata
        self._toolbar.set_metadata(
            f"{meta.resolution}  |  {meta.codec}  |  "
            f"{meta.fps} fps  |  {meta.duration_str}  |  {meta.size_str}"
        )

        # Status bar
        fname = os.path.basename(path)
        self._status.set_status(f"Loaded: {fname}", COLORS["success"])
        self._status.set_info(f"{meta.resolution} \u2022 {meta.size_str}")

        Toast(self, f"Opened {fname}", "success")

    # ── Playback controls ────────────────────────────────────────

    def _toggle_play(self):
        if not self._state.loaded:
            return
        self._preview.toggle()

    def _step_frames(self, delta: int):
        if not self._state.loaded:
            return
        self._preview.step_frames(delta)

    def _jump_seconds(self, seconds: float):
        if not self._state.loaded:
            return
        target = max(0, min(
            self._state.current_time + seconds,
            self._state.duration,
        ))
        self._preview.seek_time(target)

    # ── Timeline / trim interaction ──────────────────────────────

    def _on_timeline_seek(self, time_sec: float):
        if not self._state.loaded:
            return
        self._preview.seek_time(time_sec)

    def _on_frame_update(self, frame_num: int):
        """Called ~30fps during playback to update the timeline playhead."""
        self._timeline.update_playhead(frame_num)

    def _set_trim_in(self):
        if not self._state.loaded:
            return
        self._state.trim_start = self._state.current_time
        self._trim_ctrl.update_display()
        self._timeline._draw_overlays()
        Toast(self, f"IN set to {format_time(self._state.trim_start)}", "info")

    def _set_trim_out(self):
        if not self._state.loaded:
            return
        self._state.trim_end = self._state.current_time
        self._trim_ctrl.update_display()
        self._timeline._draw_overlays()
        Toast(self, f"OUT set to {format_time(self._state.trim_end)}", "info")

    def _on_trim_change(self, start: float, end: float):
        """Called when trim handles are dragged or timecodes are entered."""
        self._trim_ctrl.update_display()
        self._timeline._draw_overlays()

    # ── Export ───────────────────────────────────────────────────

    def _open_export(self):
        if not self._state.loaded:
            Toast(self, "No video loaded", "warning")
            return
        ExportDialog(
            self, self._state,
            on_done=self._on_export_done,
            on_error=self._on_export_error,
        )

    def _on_export_done(self, output_path: str):
        Toast(self, f"Exported: {os.path.basename(output_path)}", "success")
        self._status.set_status("Export complete", COLORS["success"])

    def _on_export_error(self, error: str):
        Toast(self, f"Export failed: {error}", "error")
        self._status.set_status("Export failed", COLORS["error"])

    def destroy(self):
        self._preview.stop()
        self._state.release()
        super().destroy()
