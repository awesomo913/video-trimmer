"""One row in the batch file list — name, duration, status badge, progress."""

from __future__ import annotations

import customtkinter as ctk

from config import COLORS, FONT_UI_SMALL, FONT_MONO_SMALL
from services.batch_split_service import (
    BatchFileEntry,
    STATUS_PENDING, STATUS_RUNNING, STATUS_DONE,
    STATUS_SKIPPED, STATUS_FAILED, STATUS_UNREADABLE,
)
from services.ffmpeg_service import format_time


_STATUS_COLORS = {
    STATUS_PENDING:    COLORS["text_dim"],
    STATUS_RUNNING:    COLORS["warning"],
    STATUS_DONE:       COLORS["success"],
    STATUS_SKIPPED:    COLORS["text_dim"],
    STATUS_FAILED:     COLORS["error"],
    STATUS_UNREADABLE: COLORS["error"],
}

_STATUS_TEXT = {
    STATUS_PENDING:    "pending",
    STATUS_RUNNING:    "running",
    STATUS_DONE:       "done",
    STATUS_SKIPPED:    "skipped",
    STATUS_FAILED:     "failed",
    STATUS_UNREADABLE: "unreadable",
}


def _truncate(s: str, n: int = 50) -> str:
    return s if len(s) <= n else s[:n - 3] + "..."


class BatchFileRow(ctk.CTkFrame):
    """One row: filename, duration, status badge, thin progress bar."""

    def __init__(self, master, entry: BatchFileEntry, **kwargs):
        super().__init__(master, fg_color=COLORS["bg_light"],
                         corner_radius=4, height=42, **kwargs)
        self._entry = entry
        self.pack_propagate(False)

        # Filename (left)
        self._name_label = ctk.CTkLabel(
            self, text=_truncate(entry.name),
            font=FONT_UI_SMALL, text_color=COLORS["text"],
            anchor="w",
        )
        self._name_label.pack(side="left", padx=(10, 4), pady=4)

        # Duration (mono, dim)
        dur_text = format_time(entry.duration) if entry.duration > 0 else "--"
        self._dur_label = ctk.CTkLabel(
            self, text=dur_text,
            font=FONT_MONO_SMALL, text_color=COLORS["text_dim"],
            width=80, anchor="w",
        )
        self._dur_label.pack(side="left", padx=4)

        # Status badge (right)
        status = entry.status if entry.status != STATUS_PENDING or not entry.meta_error else STATUS_UNREADABLE
        self._status_label = ctk.CTkLabel(
            self, text=_STATUS_TEXT.get(status, status),
            font=FONT_UI_SMALL, text_color=_STATUS_COLORS.get(status, COLORS["text"]),
            width=80, anchor="e",
        )
        self._status_label.pack(side="right", padx=10)

        # Progress bar (thin, hidden until running)
        self._progress = ctk.CTkProgressBar(
            self, width=140, height=6,
            fg_color=COLORS["bg"],
            progress_color=COLORS["accent"],
        )
        self._progress.set(0)
        # Will be packed/unpacked as needed
        self._progress_packed = False

    def update_from(self, entry: BatchFileEntry) -> None:
        """Re-render after status/progress change."""
        self._entry = entry
        status = entry.status
        if status == STATUS_PENDING and entry.meta_error:
            status = STATUS_UNREADABLE

        self._status_label.configure(
            text=_STATUS_TEXT.get(status, status),
            text_color=_STATUS_COLORS.get(status, COLORS["text"]),
        )

        if status == STATUS_RUNNING:
            self._progress.set(entry.progress / 100.0)
            if not self._progress_packed:
                self._progress.pack(side="right", padx=10)
                self._progress_packed = True
        else:
            if self._progress_packed:
                self._progress.pack_forget()
                self._progress_packed = False
