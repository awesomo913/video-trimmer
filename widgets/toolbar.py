"""Top toolbar — app branding, open file, metadata summary."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from config import COLORS, FONT_TITLE, FONT_UI, FONT_UI_SMALL, FONT_MONO_SMALL, APP_NAME


class Toolbar(ctk.CTkFrame):
    """Horizontal toolbar with branding, buttons, and metadata display."""

    def __init__(self, master, on_open: Callable, on_export: Callable, **kwargs):
        super().__init__(master, height=44, fg_color=COLORS["bg_light"], **kwargs)
        self.pack_propagate(False)

        # ── Left: branding ────────────────────────────────────────
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left", padx=10)

        ctk.CTkLabel(
            left, text=APP_NAME,
            font=FONT_TITLE, text_color=COLORS["accent"],
        ).pack(side="left")

        # Separator
        sep = ctk.CTkFrame(self, width=2, height=28, fg_color=COLORS["text_dim"])
        sep.pack(side="left", padx=8)

        # ── Center: action buttons ────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="left", padx=4)

        self._btn_open = ctk.CTkButton(
            btn_frame, text="\U0001F4C2 Open",
            font=FONT_UI, width=90, height=30,
            fg_color=COLORS["bg_surface"],
            hover_color=COLORS["accent"],
            command=on_open,
        )
        self._btn_open.pack(side="left", padx=4)

        self._btn_export = ctk.CTkButton(
            btn_frame, text="\U0001F4BE Export",
            font=FONT_UI, width=90, height=30,
            fg_color=COLORS["bg_surface"],
            hover_color=COLORS["success"],
            command=on_export,
        )
        self._btn_export.pack(side="left", padx=4)

        # ── Right: metadata display ──────────────────────────────
        self._meta_label = ctk.CTkLabel(
            self, text="No file loaded",
            font=FONT_MONO_SMALL,
            text_color=COLORS["text_dim"],
            anchor="e",
        )
        self._meta_label.pack(side="right", padx=12)

        # Keyboard hints
        hints = ctk.CTkLabel(
            self, text="Ctrl+O: Open  |  Ctrl+E: Export  |  Space: Play/Pause",
            font=("Segoe UI", 9),
            text_color=COLORS["text_dim"],
            anchor="e",
        )
        hints.pack(side="right", padx=8)

    def set_metadata(self, text: str):
        self._meta_label.configure(text=text, text_color=COLORS["text"])
