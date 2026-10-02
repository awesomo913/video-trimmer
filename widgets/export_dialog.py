"""Export dialog — format/quality selection, progress bar, cancel button."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from tkinter import filedialog, messagebox

import customtkinter as ctk

from config import (
    COLORS,
    EXPORT_FORMATS,
    FONT_MONO,
    FONT_UI,
    FONT_UI_BOLD,
    FONT_UI_SMALL,
    QUALITY_PRESETS,
)
from services.edit_transforms import edits_active, ffmpeg_vf_chain
from services.ffmpeg_service import TrimJob, format_time, run_trim
from services.fsutil import same_file, unique_path
from services.ui_bridge import MainThreadDispatcher
from services.video_service import VideoState

log = logging.getLogger(__name__)


class ExportDialog(ctk.CTkToplevel):
    """Modal dialog for configuring and running a video export."""

    def __init__(self, master, state: VideoState,
                 on_done: Callable[[str], None] | None = None,
                 on_error: Callable[[str], None] | None = None):
        super().__init__(master)
        self._state = state
        self._on_done = on_done
        self._on_error = on_error
        self._job: TrimJob | None = None
        self._bridge = MainThreadDispatcher(self.after, self.winfo_exists)
        self._bridge.start()
        self.protocol("WM_DELETE_WINDOW", self._cancel)

        self.title("Export Trimmed Video")
        self.geometry("480x460")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg"])
        self.transient(master)
        self.grab_set()

        self._build_ui()
        self.after(100, self.focus_force)

    def _build_ui(self):
        pad = {"padx": 16, "pady": (6, 0)}

        # ── Trim summary ─────────────────────────────────────────
        summary = ctk.CTkFrame(self, fg_color=COLORS["bg_light"], corner_radius=8)
        summary.pack(fill="x", padx=16, pady=(16, 8))

        dur = self._state.trim_end - self._state.trim_start
        has_edits = edits_active(self._state)
        ctk.CTkLabel(
            summary,
            text=f"Trim: {format_time(self._state.trim_start)} \u2192 "
                 f"{format_time(self._state.trim_end)}  "
                 f"({format_time(dur)})",
            font=FONT_MONO, text_color=COLORS["text"],
        ).pack(padx=12, pady=(8, 8 if not has_edits else 4))

        if has_edits:
            ctk.CTkLabel(
                summary,
                text="Edits (crop / rotate / flip) are baked in. Video will be re-encoded; "
                     "audio can still be copied if you choose Copy quality.",
                font=FONT_UI_SMALL,
                text_color=COLORS["warning"],
                wraplength=430,
                justify="left",
            ).pack(padx=12, pady=(0, 8))

        # ── Format ───────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="Output Format", font=FONT_UI_BOLD,
            text_color=COLORS["text"],
        ).pack(anchor="w", **pad)

        self._format_var = ctk.StringVar(value=list(EXPORT_FORMATS.keys())[0])
        ctk.CTkOptionMenu(
            self, values=list(EXPORT_FORMATS.keys()),
            variable=self._format_var,
            width=300, height=32,
            fg_color=COLORS["bg_surface"],
            button_color=COLORS["bg_surface"],
            button_hover_color=COLORS["accent"],
            font=FONT_UI,
        ).pack(anchor="w", padx=16, pady=4)

        # ── Quality ──────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="Quality Preset", font=FONT_UI_BOLD,
            text_color=COLORS["text"],
        ).pack(anchor="w", **pad)

        self._quality_var = ctk.StringVar(value=list(QUALITY_PRESETS.keys())[0])
        ctk.CTkOptionMenu(
            self, values=list(QUALITY_PRESETS.keys()),
            variable=self._quality_var,
            width=300, height=32,
            fg_color=COLORS["bg_surface"],
            button_color=COLORS["bg_surface"],
            button_hover_color=COLORS["accent"],
            font=FONT_UI,
        ).pack(anchor="w", padx=16, pady=4)

        # ── Audio toggle ─────────────────────────────────────────
        self._audio_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            self, text="Include audio",
            variable=self._audio_var,
            font=FONT_UI,
            text_color=COLORS["text"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent"],
        ).pack(anchor="w", padx=16, pady=(10, 0))

        # ── Progress bar ─────────────────────────────────────────
        self._progress = ctk.CTkProgressBar(
            self, width=400, height=14,
            fg_color=COLORS["bg_light"],
            progress_color=COLORS["success"],
        )
        self._progress.pack(padx=16, pady=(16, 4))
        self._progress.set(0)

        self._progress_label = ctk.CTkLabel(
            self, text="", font=FONT_UI_SMALL,
            text_color=COLORS["text_dim"],
        )
        self._progress_label.pack()

        # ── Buttons ──────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=(12, 16))

        self._btn_export = ctk.CTkButton(
            btn_frame, text="Export", width=120, height=36,
            font=FONT_UI_BOLD,
            fg_color=COLORS["success"],
            hover_color="#3db88a",
            text_color="#ffffff",
            command=self._start_export,
        )
        self._btn_export.pack(side="left", padx=(0, 8))

        self._btn_cancel = ctk.CTkButton(
            btn_frame, text="Cancel", width=100, height=36,
            font=FONT_UI,
            fg_color=COLORS["bg_surface"],
            hover_color=COLORS["error"],
            command=self._cancel,
        )
        self._btn_cancel.pack(side="left")

    def _start_export(self):
        # Ask for save location
        fmt_key = self._format_var.get()
        fmt = EXPORT_FORMATS[fmt_key]
        ext = fmt["ext"]

        src_dir = os.path.dirname(self._state.path)
        src_name = os.path.splitext(os.path.basename(self._state.path))[0]
        # Suggest a name that does not exist yet, so Save never lands on an old export.
        suggested = os.path.join(src_dir, f"{src_name}_trimmed{ext}")
        default_name = os.path.basename(unique_path(suggested))

        output_path = filedialog.asksaveasfilename(
            parent=self,
            title="Save Trimmed Video",
            initialdir=src_dir or None,
            initialfile=default_name,
            defaultextension=ext,
            filetypes=[(fmt_key.strip(), f"*{ext}"), ("All Files", "*.*")],
        )
        if not output_path:
            return

        # Never let the export overwrite the source file being trimmed.
        if same_file(output_path, self._state.path):
            messagebox.showwarning(
                "Invalid destination",
                "Pick a different file — you can't export over the video you're trimming.",
                parent=self,
            )
            return

        # Build job
        quality = QUALITY_PRESETS[self._quality_var.get()]
        vf = ffmpeg_vf_chain(self._state)
        self._job = TrimJob(
            input_path=self._state.path,
            output_path=output_path,
            start=self._state.trim_start,
            end=self._state.trim_end,
            copy_streams=quality["copy"],
            crf=quality["crf"],
            include_audio=self._audio_var.get(),
            video_filter=vf,
            source_duration=self._state.duration,
        )

        self._btn_export.configure(state="disabled")
        self._progress_label.configure(text="Exporting...")

        run_trim(
            self._job,
            on_progress=lambda p: self._bridge.post(self._update_progress, p),
            on_done=lambda j: self._bridge.post(self._on_export_done, j),
        )

    def _update_progress(self, pct: float):
        self._progress.set(pct / 100.0)
        self._progress_label.configure(text=f"Exporting... {pct:.1f}%")

    def _on_export_done(self, job: TrimJob):
        self._btn_export.configure(state="normal")
        if job.error == "Cancelled":
            self._close()
            return
        if job.error:
            log.warning("export failed: %s", job.error)
            self._progress_label.configure(
                text=f"Failed: {job.error}", text_color=COLORS["error"],
            )
            if self._on_error:
                self._on_error(job.error)
        else:
            self._progress.set(1.0)
            self._progress_label.configure(
                text="Export complete!", text_color=COLORS["success"],
            )
            if self._on_done:
                self._on_done(job.output_path)
            self.after(1500, self._close)

    def _cancel(self):
        if self._job and not self._job.done:
            self._job.cancel_event.set()
            self._progress_label.configure(text="Cancelling...")
        else:
            self._close()

    def _close(self):
        self._bridge.close()
        if self.winfo_exists():
            self.destroy()
