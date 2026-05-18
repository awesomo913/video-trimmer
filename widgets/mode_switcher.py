"""Mode switcher — segmented Single/Batch toggle at top of window."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from config import COLORS, FONT_UI_BOLD


class ModeSwitcher(ctk.CTkFrame):
    """Two-button segmented control. Active button gets accent color."""

    def __init__(self, master, on_mode_change: Callable[[str], None], **kwargs):
        super().__init__(master, fg_color=COLORS["bg"], height=40, **kwargs)
        self.pack_propagate(False)
        self._on_mode_change = on_mode_change
        self._mode = "single"

        # Centered container
        inner = ctk.CTkFrame(self, fg_color=COLORS["bg_light"], corner_radius=8)
        inner.pack(pady=4)

        self._btn_single = ctk.CTkButton(
            inner, text="Single",
            font=FONT_UI_BOLD, width=110, height=30,
            fg_color=COLORS["accent"], hover_color=COLORS["accent"],
            text_color="#ffffff",
            command=lambda: self._switch("single"),
        )
        self._btn_single.pack(side="left", padx=4, pady=4)

        self._btn_batch = ctk.CTkButton(
            inner, text="Batch Split",
            font=FONT_UI_BOLD, width=110, height=30,
            fg_color=COLORS["bg_surface"], hover_color=COLORS["accent"],
            text_color=COLORS["text"],
            command=lambda: self._switch("batch"),
        )
        self._btn_batch.pack(side="left", padx=4, pady=4)

    def _switch(self, mode: str) -> None:
        if mode == self._mode:
            return
        self._mode = mode
        self._refresh_buttons()
        self._on_mode_change(mode)

    def _refresh_buttons(self) -> None:
        if self._mode == "single":
            self._btn_single.configure(fg_color=COLORS["accent"], text_color="#ffffff")
            self._btn_batch.configure(fg_color=COLORS["bg_surface"], text_color=COLORS["text"])
        else:
            self._btn_batch.configure(fg_color=COLORS["accent"], text_color="#ffffff")
            self._btn_single.configure(fg_color=COLORS["bg_surface"], text_color=COLORS["text"])

    @property
    def mode(self) -> str:
        return self._mode
