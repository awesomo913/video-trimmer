"""Batch panel — top-level UI for the Batch mode.

Layout (top to bottom):
- Folder picker row
- Scrollable list of BatchFileRow
- SplitConfigPanel
- Start / Cancel button row
- Overall progress bar + status label
"""

from __future__ import annotations

import os
import threading
from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

from config import COLORS, FONT_UI, FONT_UI_SMALL, FONT_UI_BOLD, FONT_MONO
from services.batch_split_service import (
    BatchFileEntry, BatchSplitJob, ScanError,
    scan_folder, run_batch, default_output_folder,
    STATUS_RUNNING, STATUS_DONE, STATUS_FAILED, STATUS_SKIPPED,
)
from widgets.batch_file_row import BatchFileRow
from widgets.split_config_panel import SplitConfigPanel
from widgets.toast import Toast


def _truncate_path(path: str, n: int = 70) -> str:
    if len(path) <= n:
        return path
    return "..." + path[-(n - 3):]


class BatchPanel(ctk.CTkFrame):
    """Self-contained widget swapped into the main window in Batch mode."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLORS["bg"], **kwargs)

        self._folder: str = ""
        self._entries: list[BatchFileEntry] = []
        self._rows: dict[str, BatchFileRow] = {}
        self._job: BatchSplitJob | None = None
        self._scanning = False
        self._running = False

        self._build_ui()

    # ── UI construction ─────────────────────────────────────────

    def _build_ui(self) -> None:
        # ── Folder row ──────────────────────────────────────────
        folder_row = ctk.CTkFrame(self, fg_color=COLORS["bg_light"], corner_radius=8)
        folder_row.pack(fill="x", padx=12, pady=(12, 6))

        self._btn_folder = ctk.CTkButton(
            folder_row, text="\U0001F4C1 Choose Folder",
            font=FONT_UI, width=140, height=32,
            fg_color=COLORS["bg_surface"],
            hover_color=COLORS["accent"],
            command=self._pick_folder,
        )
        self._btn_folder.pack(side="left", padx=10, pady=8)

        self._folder_label = ctk.CTkLabel(
            folder_row, text="No folder selected",
            font=FONT_MONO, text_color=COLORS["text_dim"],
            anchor="w",
        )
        self._folder_label.pack(side="left", fill="x", expand=True, padx=6)

        self._count_label = ctk.CTkLabel(
            folder_row, text="",
            font=FONT_UI_SMALL, text_color=COLORS["accent"],
            anchor="e",
        )
        self._count_label.pack(side="right", padx=10)

        # ── File list (scrollable) ──────────────────────────────
        list_container = ctk.CTkFrame(self, fg_color=COLORS["bg_light"], corner_radius=8)
        list_container.pack(fill="both", expand=True, padx=12, pady=6)

        ctk.CTkLabel(
            list_container, text="Videos found in folder",
            font=FONT_UI_BOLD, text_color=COLORS["text"],
            anchor="w",
        ).pack(fill="x", padx=10, pady=(8, 4))

        self._scroll = ctk.CTkScrollableFrame(
            list_container, fg_color="transparent",
            scrollbar_button_color=COLORS["bg_surface"],
            scrollbar_button_hover_color=COLORS["accent"],
        )
        self._scroll.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        self._empty_label = ctk.CTkLabel(
            self._scroll,
            text="Pick a folder to scan for videos.",
            font=FONT_UI_SMALL, text_color=COLORS["text_dim"],
        )
        self._empty_label.pack(pady=20)

        # ── Split config ────────────────────────────────────────
        self._config_panel = SplitConfigPanel(self)
        self._config_panel.pack(fill="x", padx=12, pady=6)

        # ── Action buttons + progress ───────────────────────────
        action_row = ctk.CTkFrame(self, fg_color="transparent")
        action_row.pack(fill="x", padx=12, pady=(6, 4))

        self._btn_start = ctk.CTkButton(
            action_row, text="Start Batch Split",
            font=FONT_UI_BOLD, width=180, height=36,
            fg_color=COLORS["success"], hover_color="#3db88a",
            text_color="#ffffff",
            command=self._start,
            state="disabled",
        )
        self._btn_start.pack(side="left", padx=(0, 8))

        self._btn_cancel = ctk.CTkButton(
            action_row, text="Cancel",
            font=FONT_UI, width=100, height=36,
            fg_color=COLORS["bg_surface"], hover_color=COLORS["error"],
            command=self._cancel,
            state="disabled",
        )
        self._btn_cancel.pack(side="left")

        self._overall_label = ctk.CTkLabel(
            action_row, text="",
            font=FONT_UI_SMALL, text_color=COLORS["text_dim"],
            anchor="e",
        )
        self._overall_label.pack(side="right", padx=8)

        progress_row = ctk.CTkFrame(self, fg_color="transparent")
        progress_row.pack(fill="x", padx=12, pady=(0, 12))

        self._overall_progress = ctk.CTkProgressBar(
            progress_row, height=12,
            fg_color=COLORS["bg_light"],
            progress_color=COLORS["success"],
        )
        self._overall_progress.set(0)
        self._overall_progress.pack(fill="x")

    # ── Folder pick + scan ──────────────────────────────────────

    def _pick_folder(self) -> None:
        if self._scanning or self._running:
            return
        path = filedialog.askdirectory(title="Choose folder of videos to split")
        if not path:
            return
        self._folder = path
        self._folder_label.configure(
            text=_truncate_path(path), text_color=COLORS["text"],
        )
        self._count_label.configure(text="Scanning...")
        self._scanning = True
        self._btn_start.configure(state="disabled")
        threading.Thread(target=self._scan_worker, args=(path,), daemon=True).start()

    def _scan_worker(self, path: str) -> None:
        try:
            entries = scan_folder(path)
            self.after(0, self._on_scan_done, entries, "")
        except ScanError as exc:
            self.after(0, self._on_scan_done, [], str(exc))

    def _on_scan_done(self, entries: list[BatchFileEntry], error: str) -> None:
        self._scanning = False
        self._entries = entries
        self._populate_rows()

        if error:
            self._count_label.configure(text="Folder unreadable", text_color=COLORS["error"])
            self._btn_start.configure(state="disabled")
            Toast(self, f"Cannot scan folder: {error}", "error")
            return

        playable = [e for e in entries if e.duration > 0]
        n = len(entries)
        if n == 0:
            self._count_label.configure(text="No videos found", text_color=COLORS["warning"])
            self._btn_start.configure(state="disabled")
        else:
            self._count_label.configure(
                text=f"{n} video{'s' if n != 1 else ''} found ({len(playable)} playable)",
                text_color=COLORS["accent"],
            )
            self._btn_start.configure(state="normal" if playable else "disabled")

    def _populate_rows(self) -> None:
        # Clear existing rows
        for child in self._scroll.winfo_children():
            child.destroy()
        self._rows.clear()

        if not self._entries:
            self._empty_label = ctk.CTkLabel(
                self._scroll,
                text="No video files in this folder.",
                font=FONT_UI_SMALL, text_color=COLORS["text_dim"],
            )
            self._empty_label.pack(pady=20)
            return

        for entry in self._entries:
            row = BatchFileRow(self._scroll, entry)
            row.pack(fill="x", padx=4, pady=2)
            self._rows[entry.path] = row

    # ── Run / cancel ────────────────────────────────────────────

    def _start(self) -> None:
        if self._running or not self._entries:
            return

        config = self._config_panel.get_config()
        output_folder = default_output_folder(self._folder)
        self._job = BatchSplitJob(
            input_folder=self._folder,
            output_folder=output_folder,
            files=self._entries,
            config=config,
        )

        # Reset row UI
        for entry in self._entries:
            if entry.status not in ("unreadable",):
                entry.status = "pending"
                entry.progress = 0.0
                entry.parts_done = 0
                entry.error = ""
            row = self._rows.get(entry.path)
            if row:
                row.update_from(entry)

        self._running = True
        self._overall_progress.set(0)
        self._set_running_ui(True)
        self._update_overall(0, 0, "")

        run_batch(
            self._job,
            on_file_start=lambda e: self.after(0, self._on_file_start, e),
            on_file_progress=lambda e: self.after(0, self._on_file_progress, e),
            on_file_done=lambda e: self.after(0, self._on_file_done, e),
            on_batch_done=lambda j, err: self.after(0, self._on_batch_done, j, err),
        )

    def _cancel(self) -> None:
        if not self._job or not self._running:
            return
        self._job.cancel_event.set()
        self._overall_label.configure(text="Cancelling...", text_color=COLORS["warning"])

    def _set_running_ui(self, running: bool) -> None:
        if running:
            self._btn_start.configure(state="disabled")
            self._btn_cancel.configure(state="normal")
            self._btn_folder.configure(state="disabled")
            self._config_panel.set_enabled(False)
        else:
            self._btn_start.configure(state="normal" if self._entries else "disabled")
            self._btn_cancel.configure(state="disabled")
            self._btn_folder.configure(state="normal")
            self._config_panel.set_enabled(True)

    # ── Service callbacks (main thread via after) ───────────────

    def _on_file_start(self, entry: BatchFileEntry) -> None:
        row = self._rows.get(entry.path)
        if row:
            row.update_from(entry)
        self._refresh_overall(entry)

    def _on_file_progress(self, entry: BatchFileEntry) -> None:
        row = self._rows.get(entry.path)
        if row:
            row.update_from(entry)
        self._refresh_overall(entry)

    def _on_file_done(self, entry: BatchFileEntry) -> None:
        row = self._rows.get(entry.path)
        if row:
            row.update_from(entry)
        self._refresh_overall(entry)

    def _on_batch_done(self, job: BatchSplitJob, error: str) -> None:
        self._running = False
        self._set_running_ui(False)

        n_done = sum(1 for e in job.files if e.status == STATUS_DONE)
        n_failed = sum(1 for e in job.files if e.status == STATUS_FAILED)
        n_skipped = sum(1 for e in job.files if e.status == STATUS_SKIPPED)
        n_total = len(job.files)

        if error == "cancelled":
            self._overall_label.configure(
                text=f"Cancelled — {n_done}/{n_total} complete",
                text_color=COLORS["warning"],
            )
            Toast(self, f"Batch cancelled — {n_done}/{n_total} done", "warning")
        elif error:
            self._overall_label.configure(
                text=f"Error: {error}", text_color=COLORS["error"],
            )
            Toast(self, f"Batch error: {error}", "error")
        else:
            self._overall_progress.set(1.0)
            summary = f"Done — {n_done}/{n_total}"
            if n_failed:
                summary += f", {n_failed} failed"
            if n_skipped:
                summary += f", {n_skipped} skipped"
            self._overall_label.configure(
                text=summary, text_color=COLORS["success"],
            )
            try:
                os.startfile(job.output_folder)  # nosec - opens explorer to results
            except OSError as exc:
                # Best-effort — batch already succeeded, just couldn't open Explorer
                Toast(self, f"Outputs ready but couldn't open folder: {exc}", "warning")
            Toast(self, f"Batch complete — outputs in {os.path.basename(job.output_folder)}/", "success")

    # ── Overall progress ────────────────────────────────────────

    def _refresh_overall(self, _entry: BatchFileEntry | None = None) -> None:
        if not self._job:
            return
        # Compute weighted total: each file = 1 unit. Done = 1, running = file_progress/100
        total = 0
        progress = 0.0
        for e in self._job.files:
            if e.status == "unreadable":
                continue
            total += 1
            if e.status == STATUS_DONE:
                progress += 1.0
            elif e.status == STATUS_SKIPPED:
                progress += 1.0  # counted as complete-ish
            elif e.status == STATUS_RUNNING:
                progress += e.progress / 100.0

        if total == 0:
            return
        pct = progress / total
        self._overall_progress.set(pct)
        current = next((e for e in self._job.files if e.status == STATUS_RUNNING), None)
        if current:
            self._overall_label.configure(
                text=f"{int(pct * 100)}%  —  {current.name}  ({current.parts_done}/{current.parts_total})",
                text_color=COLORS["accent"],
            )

    def _update_overall(self, _done: int, _total: int, _msg: str) -> None:
        self._overall_label.configure(text="Starting...", text_color=COLORS["text_dim"])
