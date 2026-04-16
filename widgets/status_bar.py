"""Bottom status bar — shows status text, file info, and duration."""

from __future__ import annotations

import customtkinter as ctk

from config import COLORS, FONT_UI_SMALL, FONT_MONO_SMALL


class StatusBar(ctk.CTkFrame):
    """Bottom bar with left status text and right-aligned file info."""

    def __init__(self, master, **kwargs):
        super().__init__(master, height=28, fg_color=COLORS["bg_light"], **kwargs)
        self.pack_propagate(False)

        self._status = ctk.CTkLabel(
            self, text="Ready", font=FONT_UI_SMALL,
            text_color=COLORS["text_dim"], anchor="w",
        )
        self._status.pack(side="left", padx=10)

        self._info = ctk.CTkLabel(
            self, text="", font=FONT_MONO_SMALL,
            text_color=COLORS["text_dim"], anchor="e",
        )
        self._info.pack(side="right", padx=10)

    def set_status(self, text: str, color: str | None = None):
        self._status.configure(
            text=text,
            text_color=color or COLORS["text_dim"],
        )

    def set_info(self, text: str):
        self._info.configure(text=text)
