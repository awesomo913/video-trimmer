"""Non-blocking toast notification — slides in from top-right, auto-dismisses."""

from __future__ import annotations

import customtkinter as ctk

from config import COLORS, FONT_UI_SMALL

_TYPE_COLORS = {
    "success": COLORS["success"],
    "error":   COLORS["error"],
    "warning": COLORS["warning"],
    "info":    COLORS["bg_surface"],
}

_TYPE_DURATION = {
    "success": 3000,
    "error":   5000,
    "warning": 4000,
    "info":    3000,
}


class Toast(ctk.CTkFrame):
    """Ephemeral toast that appears top-right and auto-dismisses."""

    _active: list[Toast] = []  # class-level stack for positioning

    def __init__(self, parent: ctk.CTkBaseClass, message: str,
                 toast_type: str = "info"):
        color = _TYPE_COLORS.get(toast_type, _TYPE_COLORS["info"])
        super().__init__(
            parent,
            fg_color=color,
            corner_radius=8,
            border_width=0,
        )

        self._label = ctk.CTkLabel(
            self, text=message,
            font=FONT_UI_SMALL,
            text_color="#ffffff",
            wraplength=300,
            anchor="w",
        )
        self._label.pack(padx=12, pady=8)

        # Close button
        close_btn = ctk.CTkButton(
            self, text="\u2715", width=24, height=24,
            fg_color="transparent", hover_color="#ffffff30",
            text_color="#ffffff", font=("Segoe UI", 10),
            command=self._dismiss,
        )
        close_btn.place(relx=1.0, rely=0, x=-28, y=4)

        # Position
        slot = len(Toast._active)
        Toast._active.append(self)
        self.place(relx=1.0, x=-10, y=10 + slot * 52, anchor="ne")

        # Auto-dismiss
        duration = _TYPE_DURATION.get(toast_type, 3000)
        self._dismiss_id = self.after(duration, self._dismiss)

    def _dismiss(self):
        if hasattr(self, "_dismiss_id"):
            self.after_cancel(self._dismiss_id)
        if self in Toast._active:
            Toast._active.remove(self)
        self.destroy()
        # Reposition remaining toasts
        for i, t in enumerate(Toast._active):
            t.place_configure(y=10 + i * 52)
