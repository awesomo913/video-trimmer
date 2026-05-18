"""Split configuration panel — mode radio, preset buttons, custom N, encode options."""

from __future__ import annotations

import customtkinter as ctk

from config import (
    COLORS, FONT_UI, FONT_UI_SMALL, FONT_UI_BOLD, FONT_MONO,
    EXPORT_FORMATS, QUALITY_PRESETS,
    SPLIT_PRESETS, SPLIT_N_MIN, SPLIT_N_MAX,
    SPLIT_DEFAULT_CHUNK_SECONDS,
)
from services.batch_split_service import SplitConfig


class SplitConfigPanel(ctk.CTkFrame):
    """Compact panel exposing all split settings as a SplitConfig."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLORS["bg_light"],
                         corner_radius=8, **kwargs)
        self._mode_var = ctk.StringVar(value="equal")
        self._n_var = ctk.IntVar(value=4)
        self._chunk_var = ctk.StringVar(value=str(SPLIT_DEFAULT_CHUNK_SECONDS))
        self._format_var = ctk.StringVar(value=list(EXPORT_FORMATS.keys())[0])
        self._quality_var = ctk.StringVar(value=list(QUALITY_PRESETS.keys())[0])
        self._audio_var = ctk.BooleanVar(value=True)
        self._preset_buttons: list[ctk.CTkButton] = []
        self._build_ui()
        self._refresh_mode_state()

    def _build_ui(self) -> None:
        # Title
        ctk.CTkLabel(
            self, text="Split Settings",
            font=FONT_UI_BOLD, text_color=COLORS["accent"],
        ).pack(anchor="w", padx=12, pady=(10, 4))

        # ── Mode radios ───────────────────────────────────────────
        mode_row = ctk.CTkFrame(self, fg_color="transparent")
        mode_row.pack(fill="x", padx=12, pady=(2, 6))

        ctk.CTkRadioButton(
            mode_row, text="Equal parts",
            variable=self._mode_var, value="equal",
            font=FONT_UI, text_color=COLORS["text"],
            fg_color=COLORS["accent"], hover_color=COLORS["accent"],
            command=self._refresh_mode_state,
        ).pack(side="left", padx=(0, 16))

        ctk.CTkRadioButton(
            mode_row, text="Duration chunks",
            variable=self._mode_var, value="duration",
            font=FONT_UI, text_color=COLORS["text"],
            fg_color=COLORS["accent"], hover_color=COLORS["accent"],
            command=self._refresh_mode_state,
        ).pack(side="left")

        # ── Equal mode controls ───────────────────────────────────
        self._equal_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._equal_frame.pack(fill="x", padx=12, pady=4)

        preset_row = ctk.CTkFrame(self._equal_frame, fg_color="transparent")
        preset_row.pack(side="left")

        ctk.CTkLabel(
            preset_row, text="Parts:",
            font=FONT_UI_SMALL, text_color=COLORS["text_dim"],
        ).pack(side="left", padx=(0, 6))

        for n in SPLIT_PRESETS:
            btn = ctk.CTkButton(
                preset_row, text=str(n), width=34, height=26,
                font=FONT_UI_SMALL,
                fg_color=COLORS["bg_surface"],
                hover_color=COLORS["accent"],
                command=lambda v=n: self._on_preset_click(v),
            )
            btn.pack(side="left", padx=2)
            self._preset_buttons.append(btn)

        # Custom N spinner
        ctk.CTkLabel(
            self._equal_frame, text="  Custom:",
            font=FONT_UI_SMALL, text_color=COLORS["text_dim"],
        ).pack(side="left", padx=(12, 4))

        self._n_entry = ctk.CTkEntry(
            self._equal_frame, width=50, height=26,
            font=FONT_MONO, text_color=COLORS["text"],
            fg_color=COLORS["bg"], justify="center",
        )
        self._n_entry.insert(0, str(self._n_var.get()))
        self._n_entry.pack(side="left")
        self._n_entry.bind("<KeyRelease>", self._on_n_entry)
        self._n_entry.bind("<FocusOut>", self._on_n_entry)

        # ── Duration mode controls ────────────────────────────────
        self._duration_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._duration_frame.pack(fill="x", padx=12, pady=4)

        ctk.CTkLabel(
            self._duration_frame, text="Chunk size:",
            font=FONT_UI_SMALL, text_color=COLORS["text_dim"],
        ).pack(side="left", padx=(0, 6))

        self._chunk_entry = ctk.CTkEntry(
            self._duration_frame, width=80, height=26,
            font=FONT_MONO, text_color=COLORS["text"],
            fg_color=COLORS["bg"],
            textvariable=self._chunk_var, justify="center",
        )
        self._chunk_entry.pack(side="left")

        ctk.CTkLabel(
            self._duration_frame, text="seconds per part",
            font=FONT_UI_SMALL, text_color=COLORS["text_dim"],
        ).pack(side="left", padx=6)

        # ── Format / Quality / Audio ─────────────────────────────
        enc_row = ctk.CTkFrame(self, fg_color="transparent")
        enc_row.pack(fill="x", padx=12, pady=(8, 4))

        ctk.CTkLabel(
            enc_row, text="Format:",
            font=FONT_UI_SMALL, text_color=COLORS["text_dim"],
        ).pack(side="left", padx=(0, 4))

        ctk.CTkOptionMenu(
            enc_row, values=list(EXPORT_FORMATS.keys()),
            variable=self._format_var,
            width=120, height=28,
            fg_color=COLORS["bg_surface"],
            button_color=COLORS["bg_surface"],
            button_hover_color=COLORS["accent"],
            font=FONT_UI_SMALL,
        ).pack(side="left", padx=(0, 12))

        ctk.CTkLabel(
            enc_row, text="Quality:",
            font=FONT_UI_SMALL, text_color=COLORS["text_dim"],
        ).pack(side="left", padx=(0, 4))

        ctk.CTkOptionMenu(
            enc_row, values=list(QUALITY_PRESETS.keys()),
            variable=self._quality_var,
            width=200, height=28,
            fg_color=COLORS["bg_surface"],
            button_color=COLORS["bg_surface"],
            button_hover_color=COLORS["accent"],
            font=FONT_UI_SMALL,
        ).pack(side="left")

        ctk.CTkCheckBox(
            enc_row, text="Include audio",
            variable=self._audio_var,
            font=FONT_UI_SMALL, text_color=COLORS["text"],
            fg_color=COLORS["accent"], hover_color=COLORS["accent"],
        ).pack(side="left", padx=12)

        self._highlight_preset()

    # ── Mode toggling ────────────────────────────────────────────

    def _refresh_mode_state(self) -> None:
        """Visually grey out the inactive group."""
        equal_active = self._mode_var.get() == "equal"
        for child in self._equal_frame.winfo_children():
            self._set_subtree_state(child, "normal" if equal_active else "disabled")
        for child in self._duration_frame.winfo_children():
            self._set_subtree_state(child, "disabled" if equal_active else "normal")

    @staticmethod
    def _set_subtree_state(widget, state: str) -> None:
        import tkinter as tk
        try:
            widget.configure(state=state)
        except tk.TclError:
            # Widget doesn't accept `state` (e.g. CTkFrame). Expected.
            pass
        for child in getattr(widget, "winfo_children", lambda: [])():
            SplitConfigPanel._set_subtree_state(child, state)

    # ── Preset buttons ───────────────────────────────────────────

    def _on_preset_click(self, n: int) -> None:
        self._n_var.set(n)
        self._n_entry.delete(0, "end")
        self._n_entry.insert(0, str(n))
        self._highlight_preset()

    def _on_n_entry(self, _event=None) -> None:
        try:
            val = int(self._n_entry.get())
        except ValueError:
            return
        val = max(SPLIT_N_MIN, min(SPLIT_N_MAX, val))
        self._n_var.set(val)
        self._highlight_preset()

    def _highlight_preset(self) -> None:
        active_n = self._n_var.get()
        for btn, n in zip(self._preset_buttons, SPLIT_PRESETS):
            if n == active_n:
                btn.configure(fg_color=COLORS["accent"])
            else:
                btn.configure(fg_color=COLORS["bg_surface"])

    # ── Public API ───────────────────────────────────────────────

    def get_config(self) -> SplitConfig:
        try:
            chunk = float(self._chunk_var.get())
        except ValueError:
            chunk = SPLIT_DEFAULT_CHUNK_SECONDS

        return SplitConfig(
            mode=self._mode_var.get(),
            n_parts=self._n_var.get(),
            chunk_seconds=chunk,
            output_format=self._format_var.get(),
            quality_key=self._quality_var.get(),
            include_audio=self._audio_var.get(),
        )

    def set_enabled(self, enabled: bool) -> None:
        """Lock the whole panel during a running batch."""
        state = "normal" if enabled else "disabled"
        for child in self.winfo_children():
            self._set_subtree_state(child, state)
        if enabled:
            self._refresh_mode_state()
