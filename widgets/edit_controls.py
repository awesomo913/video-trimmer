"""Crop / rotate / flip controls wired to VideoState."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from config import COLORS, FONT_UI, FONT_UI_SMALL, FONT_UI_BOLD
from services.video_service import VideoState


class EditControls(ctk.CTkFrame):
    """Transforms applied to preview and to exported video."""

    def __init__(
        self,
        master,
        state: VideoState,
        on_edit_change: Callable[[], None],
        **kwargs,
    ):
        super().__init__(master, fg_color=COLORS["bg_light"], corner_radius=8, **kwargs)
        self._state = state
        self._on_edit_change = on_edit_change

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=10, pady=(8, 4))

        ctk.CTkLabel(
            head,
            text="Edit",
            font=FONT_UI_BOLD,
            text_color=COLORS["accent"],
        ).pack(side="left")

        ctk.CTkButton(
            head,
            text="Reset edits",
            width=100,
            height=26,
            font=FONT_UI_SMALL,
            fg_color=COLORS["bg_surface"],
            hover_color=COLORS["accent"],
            command=self._reset_all,
        ).pack(side="right")

        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(row1, text="Rotate", font=FONT_UI_SMALL, text_color=COLORS["text_dim"]).pack(
            side="left", padx=(0, 8)
        )
        self._rot_var = ctk.StringVar(value="0°")
        ctk.CTkOptionMenu(
            row1,
            values=["0°", "90° CW", "180°", "270° CW"],
            variable=self._rot_var,
            width=110,
            height=28,
            fg_color=COLORS["bg_surface"],
            button_color=COLORS["bg_surface"],
            button_hover_color=COLORS["accent"],
            font=FONT_UI_SMALL,
            command=self._on_rotate,
        ).pack(side="left", padx=4)

        self._flip_h_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            row1,
            text="Flip H",
            variable=self._flip_h_var,
            font=FONT_UI_SMALL,
            text_color=COLORS["text"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent"],
            command=self._sync_flips,
        ).pack(side="left", padx=(16, 4))

        self._flip_v_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            row1,
            text="Flip V",
            variable=self._flip_v_var,
            font=FONT_UI_SMALL,
            text_color=COLORS["text"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent"],
            command=self._sync_flips,
        ).pack(side="left", padx=4)

        crop_row = ctk.CTkFrame(self, fg_color="transparent")
        crop_row.pack(fill="x", padx=10, pady=(4, 4))

        self._crop_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            crop_row,
            text="Crop (inset % each edge)",
            variable=self._crop_var,
            font=FONT_UI,
            text_color=COLORS["text"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent"],
            command=self._toggle_crop,
        ).pack(anchor="w")

        self._sl_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._sl_frame.pack(fill="x", padx=10, pady=(0, 8))

        self._sl_left = self._mk_slider(self._sl_frame, "L", self._on_crop_slider)
        self._sl_top = self._mk_slider(self._sl_frame, "T", self._on_crop_slider)
        self._sl_right = self._mk_slider(self._sl_frame, "R", self._on_crop_slider)
        self._sl_bottom = self._mk_slider(self._sl_frame, "B", self._on_crop_slider)

        self._sync_from_state()
        self._update_crop_ui()

    def attach_state(self, state: VideoState):
        self._state = state
        self._sync_from_state()
        self._update_crop_ui()

    def _mk_slider(
        self,
        parent: ctk.CTkFrame,
        label: str,
        command,
    ) -> ctk.CTkSlider:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text=label, width=14, font=FONT_UI_SMALL, text_color=COLORS["text_dim"]).pack(
            side="left"
        )
        sl = ctk.CTkSlider(
            row,
            from_=0,
            to=45,
            number_of_steps=45,
            height=16,
            fg_color=COLORS["bg_surface"],
            progress_color=COLORS["success"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent"],
            command=lambda _v: command(),
        )
        sl.pack(side="left", fill="x", expand=True, padx=8)
        return sl

    def _toggle_crop(self):
        self._state.crop_enabled = self._crop_var.get()
        self._update_crop_ui()
        self._on_crop_slider()

    def _on_crop_slider(self):
        if not self._state.loaded:
            return
        self._state.crop_left_pct = float(self._sl_left.get())
        self._state.crop_top_pct = float(self._sl_top.get())
        self._state.crop_right_pct = float(self._sl_right.get())
        self._state.crop_bottom_pct = float(self._sl_bottom.get())
        self._notify()

    def _on_rotate(self, _choice: str):
        m = self._rot_var.get()
        deg = {"0°": 0, "90° CW": 90, "180°": 180, "270° CW": 270}.get(m, 0)
        self._state.rotation_cw = deg
        self._notify()

    def _sync_flips(self):
        self._state.flip_horizontal = self._flip_h_var.get()
        self._state.flip_vertical = self._flip_v_var.get()
        self._notify()

    def _notify(self):
        if self._on_edit_change:
            self._on_edit_change()

    def _reset_all(self):
        self._state.crop_enabled = False
        self._state.crop_left_pct = 0.0
        self._state.crop_top_pct = 0.0
        self._state.crop_right_pct = 0.0
        self._state.crop_bottom_pct = 0.0
        self._state.rotation_cw = 0
        self._state.flip_horizontal = False
        self._state.flip_vertical = False
        self._sync_from_state()
        self._update_crop_ui()
        self._notify()

    def _sync_from_state(self):
        s = self._state
        self._crop_var.set(s.crop_enabled)
        self._sl_left.set(s.crop_left_pct)
        self._sl_top.set(s.crop_top_pct)
        self._sl_right.set(s.crop_right_pct)
        self._sl_bottom.set(s.crop_bottom_pct)
        rev = {0: "0°", 90: "90° CW", 180: "180°", 270: "270° CW"}
        self._rot_var.set(rev.get(s.rotation_cw % 360, "0°"))
        self._flip_h_var.set(s.flip_horizontal)
        self._flip_v_var.set(s.flip_vertical)

    def _update_crop_ui(self):
        enabled = self._crop_var.get() and self._state.loaded
        state_sl = "normal" if enabled else "disabled"
        for sl in (self._sl_left, self._sl_top, self._sl_right, self._sl_bottom):
            try:
                sl.configure(state=state_sl)
            except Exception:
                pass
