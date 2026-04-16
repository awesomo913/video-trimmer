"""Trim controls — timecode entries, set in/out buttons, trim duration display."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from config import COLORS, FONT_UI, FONT_UI_SMALL, FONT_MONO, FONT_UI_BOLD
from services.ffmpeg_service import format_time, parse_time
from services.video_service import VideoState


class TrimControls(ctk.CTkFrame):
    """Horizontal bar with in/out timecodes, set buttons, and trim duration."""

    def __init__(self, master, state: VideoState,
                 on_set_in: Callable[[], None] | None = None,
                 on_set_out: Callable[[], None] | None = None,
                 on_trim_change: Callable[[float, float], None] | None = None,
                 **kwargs):
        super().__init__(master, height=44, fg_color=COLORS["bg_light"], **kwargs)
        self.pack_propagate(False)
        self._state = state
        self._on_set_in = on_set_in
        self._on_set_out = on_set_out
        self._on_trim_change = on_trim_change

        # ── In point ─────────────────────────────────────────────
        in_frame = ctk.CTkFrame(self, fg_color="transparent")
        in_frame.pack(side="left", padx=8)

        ctk.CTkLabel(
            in_frame, text="IN", font=FONT_UI_BOLD,
            text_color=COLORS["handle_in"],
        ).pack(side="left", padx=(0, 4))

        self._in_entry = ctk.CTkEntry(
            in_frame, width=100, height=28,
            font=FONT_MONO, text_color=COLORS["text"],
            fg_color=COLORS["bg"], border_color=COLORS["handle_in"],
            justify="center",
        )
        self._in_entry.pack(side="left")
        self._in_entry.insert(0, "00:00.00")
        self._in_entry.bind("<Return>", self._on_in_entry)

        ctk.CTkButton(
            in_frame, text="[ Set", width=50, height=28,
            font=FONT_UI_SMALL,
            fg_color=COLORS["handle_in"],
            hover_color="#3db88a",
            text_color="#ffffff",
            command=self._set_in,
        ).pack(side="left", padx=4)

        # ── Separator ────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="\u2192", font=("Segoe UI", 16),
            text_color=COLORS["text_dim"],
        ).pack(side="left", padx=8)

        # ── Out point ────────────────────────────────────────────
        out_frame = ctk.CTkFrame(self, fg_color="transparent")
        out_frame.pack(side="left", padx=8)

        ctk.CTkLabel(
            out_frame, text="OUT", font=FONT_UI_BOLD,
            text_color=COLORS["handle_out"],
        ).pack(side="left", padx=(0, 4))

        self._out_entry = ctk.CTkEntry(
            out_frame, width=100, height=28,
            font=FONT_MONO, text_color=COLORS["text"],
            fg_color=COLORS["bg"], border_color=COLORS["handle_out"],
            justify="center",
        )
        self._out_entry.pack(side="left")
        self._out_entry.insert(0, "00:00.00")
        self._out_entry.bind("<Return>", self._on_out_entry)

        ctk.CTkButton(
            out_frame, text="] Set", width=50, height=28,
            font=FONT_UI_SMALL,
            fg_color=COLORS["handle_out"],
            hover_color="#c93a52",
            text_color="#ffffff",
            command=self._set_out,
        ).pack(side="left", padx=4)

        # ── Duration display ─────────────────────────────────────
        dur_frame = ctk.CTkFrame(self, fg_color="transparent")
        dur_frame.pack(side="left", padx=20)

        ctk.CTkLabel(
            dur_frame, text="Trim Duration:",
            font=FONT_UI_SMALL, text_color=COLORS["text_dim"],
        ).pack(side="left", padx=(0, 6))

        self._dur_label = ctk.CTkLabel(
            dur_frame, text="00:00.00",
            font=FONT_MONO, text_color=COLORS["accent"],
        )
        self._dur_label.pack(side="left")

        # ── Reset button ─────────────────────────────────────────
        ctk.CTkButton(
            self, text="Reset", width=60, height=28,
            font=FONT_UI_SMALL,
            fg_color=COLORS["bg_surface"],
            hover_color=COLORS["warning"],
            command=self._reset,
        ).pack(side="right", padx=10)

    def _set_in(self):
        if self._on_set_in:
            self._on_set_in()
        self.update_display()

    def _set_out(self):
        if self._on_set_out:
            self._on_set_out()
        self.update_display()

    def _on_in_entry(self, _event=None):
        try:
            t = parse_time(self._in_entry.get())
            t = max(0, min(t, self._state.trim_end - 0.1))
            self._state.trim_start = t
            if self._on_trim_change:
                self._on_trim_change(self._state.trim_start, self._state.trim_end)
            self.update_display()
        except (ValueError, IndexError):
            pass

    def _on_out_entry(self, _event=None):
        try:
            t = parse_time(self._out_entry.get())
            t = max(self._state.trim_start + 0.1, min(t, self._state.duration))
            self._state.trim_end = t
            if self._on_trim_change:
                self._on_trim_change(self._state.trim_start, self._state.trim_end)
            self.update_display()
        except (ValueError, IndexError):
            pass

    def _reset(self):
        self._state.trim_start = 0.0
        self._state.trim_end = self._state.duration
        if self._on_trim_change:
            self._on_trim_change(self._state.trim_start, self._state.trim_end)
        self.update_display()

    def update_display(self):
        """Refresh the timecode entries and duration from current state."""
        self._in_entry.delete(0, "end")
        self._in_entry.insert(0, format_time(self._state.trim_start))

        self._out_entry.delete(0, "end")
        self._out_entry.insert(0, format_time(self._state.trim_end))

        dur = max(0, self._state.trim_end - self._state.trim_start)
        self._dur_label.configure(text=format_time(dur))
