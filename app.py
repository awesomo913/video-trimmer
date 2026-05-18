"""Main application window — layout, keybinds, drag-and-drop, widget wiring."""

from __future__ import annotations

import os
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
from widgets.edit_controls import EditControls
from widgets.mode_switcher import ModeSwitcher
from widgets.batch_panel import BatchPanel


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
        self._mode = "single"
        self._batch_panel: BatchPanel | None = None

        # ── Layout ───────────────────────────────────────────────
        self._build_ui()
        self._bind_keys()

        # ── Drag and drop (via TkDnD if available) ───────────────
        self._setup_dnd()

    def _build_ui(self):
        # Mode switcher (very top)
        self._mode_switcher = ModeSwitcher(self, on_mode_change=self._on_mode_change)
        self._mode_switcher.pack(fill="x", side="top")

        # Toolbar
        self._toolbar = Toolbar(
            self,
            on_open=self._open_file,
            on_export=self._open_export,
            on_snapshot=self._export_snapshot,
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

        self._edit_ctrl = EditControls(
            self,
            state=self._state,
            on_edit_change=self._on_edit_change,
        )
        self._edit_ctrl.pack(fill="x", side="bottom", padx=8, pady=(0, 4))

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
        self.bind("<Control-Shift-s>", lambda e: self._export_snapshot())
        self.bind("<Control-Shift-S>", lambda e: self._export_snapshot())
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
        self._edit_ctrl.attach_state(self._state)

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

    def _on_edit_change(self):
        self._preview.refresh_after_edit()

    # ── Mode switching ───────────────────────────────────────────

    def _on_mode_change(self, mode: str) -> None:
        if mode == self._mode:
            return
        self._mode = mode
        if mode == "batch":
            self._enter_batch_mode()
        else:
            self._enter_single_mode()

    def _enter_batch_mode(self) -> None:
        # Pause playback if running
        if self._preview is not None:
            try:
                self._preview.pause()
            except Exception:
                pass
        # Hide single-mode widgets
        for w in (self._preview, self._timeline, self._trim_ctrl, self._edit_ctrl):
            try:
                w.pack_forget()
            except Exception:
                pass
        # Lazy-instantiate batch panel
        if self._batch_panel is None:
            self._batch_panel = BatchPanel(self)
        self._batch_panel.pack(fill="both", expand=True, side="top")
        self._status.set_status("Batch mode — pick a folder of videos", COLORS["accent"])

    def _enter_single_mode(self) -> None:
        if self._batch_panel is not None:
            self._batch_panel.pack_forget()
        # Re-pack single-mode widgets in their original order
        # (bottom-anchored widgets pack from bottom-up, preview takes the rest)
        self._trim_ctrl.pack(fill="x", side="bottom")
        self._timeline.pack(fill="x", side="bottom", ipady=4)
        self._edit_ctrl.pack(fill="x", side="bottom", padx=8, pady=(0, 4))
        self._preview.pack(fill="both", expand=True, side="top")
        if self._state.loaded:
            fname = os.path.basename(self._state.path)
            self._status.set_status(f"Loaded: {fname}", COLORS["success"])
        else:
            self._status.set_status("Ready")

    def _export_snapshot(self):
        if not self._state.loaded:
            Toast(self, "No video loaded", "warning")
            return
        img = self._preview.get_snapshot_image()
        if img is None:
            Toast(self, "Could not capture frame", "error")
            return
        path = filedialog.asksaveasfilename(
            title="Save frame as image",
            defaultextension=".png",
            filetypes=[
                ("PNG", "*.png"),
                ("JPEG", "*.jpg"),
                ("WebP", "*.webp"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        lower = path.lower()
        try:
            if lower.endswith((".jpg", ".jpeg")):
                img.convert("RGB").save(path, quality=95)
            elif lower.endswith(".webp"):
                img.save(path, format="WEBP", quality=90)
            else:
                img.save(path)
            Toast(self, f"Saved {os.path.basename(path)}", "success")
            self._status.set_status("Frame saved", COLORS["success"])
        except OSError as exc:
            Toast(self, f"Save failed: {exc}", "error")

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
