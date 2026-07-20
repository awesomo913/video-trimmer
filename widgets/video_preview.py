"""Video preview panel — displays OpenCV frames in a CTkLabel with playback controls."""

from __future__ import annotations

import queue
from typing import Callable

import customtkinter as ctk
from PIL import Image

from config import COLORS, FONT_UI, FONT_MONO
from services.edit_transforms import apply_pil_transforms
from services.video_service import VideoState, PlaybackEngine, read_frame_at


class VideoPreview(ctk.CTkFrame):
    """Displays the current video frame, scaled to fit the available space."""

    def __init__(self, master, state: VideoState,
                 on_frame_update: Callable[[int], None] | None = None,
                 **kwargs):
        super().__init__(master, fg_color=COLORS["bg"], **kwargs)
        self._state = state
        self._on_frame_update = on_frame_update
        self._frame_queue: queue.Queue[Image.Image] = queue.Queue(maxsize=3)
        self._engine: PlaybackEngine | None = None
        self._photo: ctk.CTkImage | None = None
        self._last_raw_frame: Image.Image | None = None
        self._polling = False

        # ── Display area ─────────────────────────────────────────
        self._canvas_frame = ctk.CTkFrame(self, fg_color="#000000", corner_radius=0)
        self._canvas_frame.pack(fill="both", expand=True, padx=4, pady=4)

        self._display = ctk.CTkLabel(
            self._canvas_frame, text="",
            fg_color="#000000",
        )
        self._display.pack(fill="both", expand=True)

        # Placeholder text
        self._placeholder = ctk.CTkLabel(
            self._canvas_frame,
            text="Open a video file to begin\nCtrl+O or drag & drop",
            font=FONT_UI,
            text_color=COLORS["text_dim"],
            fg_color="#000000",
        )
        self._placeholder.place(relx=0.5, rely=0.5, anchor="center")

        # ── Playback controls bar ────────────────────────────────
        ctrl = ctk.CTkFrame(self, height=36, fg_color=COLORS["bg_light"])
        ctrl.pack(fill="x", side="bottom")
        ctrl.pack_propagate(False)

        self._btn_play = ctk.CTkButton(
            ctrl, text="\u25B6", width=40, height=28,
            font=("Segoe UI", 14),
            fg_color=COLORS["bg_surface"],
            hover_color=COLORS["accent"],
            command=self._toggle_play,
        )
        self._btn_play.pack(side="left", padx=6, pady=4)

        # Frame step buttons
        ctk.CTkButton(
            ctrl, text="\u23EA", width=32, height=28,
            font=("Segoe UI", 12),
            fg_color=COLORS["bg_surface"],
            hover_color=COLORS["accent"],
            command=lambda: self._step(-1),
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            ctrl, text="\u23E9", width=32, height=28,
            font=("Segoe UI", 12),
            fg_color=COLORS["bg_surface"],
            hover_color=COLORS["accent"],
            command=lambda: self._step(1),
        ).pack(side="left", padx=2)

        # Timecode display
        self._time_label = ctk.CTkLabel(
            ctrl, text="00:00.00 / 00:00.00",
            font=FONT_MONO, text_color=COLORS["text"],
        )
        self._time_label.pack(side="left", padx=12)

        # Speed selector
        self._speed_var = ctk.StringVar(value="1.0x")
        speed_menu = ctk.CTkOptionMenu(
            ctrl, values=["0.25x", "0.5x", "1.0x", "1.5x", "2.0x"],
            variable=self._speed_var,
            width=70, height=28,
            fg_color=COLORS["bg_surface"],
            button_color=COLORS["bg_surface"],
            button_hover_color=COLORS["accent"],
            font=("Segoe UI", 10),
            command=self._on_speed_change,
        )
        speed_menu.pack(side="right", padx=8)

        ctk.CTkLabel(
            ctrl, text="Speed:", font=("Segoe UI", 10),
            text_color=COLORS["text_dim"],
        ).pack(side="right")

    def attach_state(self, state: VideoState):
        """Attach a new video state after opening a file."""
        self.stop()
        self._state = state
        self._last_raw_frame = None
        self._frame_queue = queue.Queue(maxsize=3)
        self._engine = PlaybackEngine(state, self._frame_queue)
        self._placeholder.place_forget()
        self._start_polling()
        # Show first frame
        self._engine.seek_frame(0)
        self._update_time_display()

    def _toggle_play(self):
        if self._engine is None:
            return
        self._engine.toggle()
        icon = "\u23F8" if self._engine.playing else "\u25B6"
        self._btn_play.configure(text=icon)

    def play(self):
        if self._engine and not self._engine.playing:
            self._toggle_play()

    def pause(self):
        if self._engine and self._engine.playing:
            self._toggle_play()

    def toggle(self):
        self._toggle_play()

    def _step(self, delta: int):
        if self._engine is None:
            return
        self._engine.step(delta)
        self._update_time_display()

    def step_frames(self, delta: int):
        self._step(delta)

    def seek_time(self, time_sec: float):
        if self._engine is None:
            return
        was_playing = self._engine.playing
        if was_playing:
            self._engine.pause()
        self._engine.seek_time(time_sec)
        self._update_time_display()
        if was_playing:
            self._engine.play()

    def seek_frame(self, frame_num: int):
        if self._engine is None:
            return
        self._engine.seek_frame(frame_num)
        self._update_time_display()

    def _on_speed_change(self, val: str):
        if self._engine is None:
            return
        speed = float(val.replace("x", ""))
        self._engine.speed = speed

    def _start_polling(self):
        if self._polling:
            return
        self._polling = True
        self._poll()

    def _poll(self):
        if not self._polling:
            return
        # Drain to the newest queued frame so the display never lags behind the
        # wall-clock-paced engine (and thus behind the audio).
        img = None
        try:
            while True:
                img = self._frame_queue.get_nowait()
        except queue.Empty:
            pass
        if img is not None:
            self._show_frame(img)
        self._update_time_display()
        if self._on_frame_update and self._state.loaded:
            self._on_frame_update(self._state.current_frame)
        # Engine can stop itself at trim-end (looping off) — keep the button in sync.
        if self._engine is not None:
            icon = "⏸" if self._engine.playing else "▶"
            self._btn_play.configure(text=icon)
        self.after(16, self._poll)

    def _show_frame(self, img: Image.Image):
        """Remember raw pixels, apply edits, scale to the label, and show."""
        self._last_raw_frame = img.copy()
        self._render_from_raw(self._last_raw_frame)

    def _render_from_raw(self, raw: Image.Image):
        """Apply crop/rotate/flip from state, then scale to fit."""
        edited = apply_pil_transforms(raw, self._state)
        dw = self._display.winfo_width()
        dh = self._display.winfo_height()
        if dw < 10 or dh < 10:
            dw, dh = 800, 450

        iw, ih = edited.size
        scale = min(dw / iw, dh / ih)
        new_w = max(1, int(iw * scale))
        new_h = max(1, int(ih * scale))

        resized = edited.resize((new_w, new_h), Image.LANCZOS)
        self._photo = ctk.CTkImage(
            light_image=resized, dark_image=resized, size=(new_w, new_h)
        )
        self._display.configure(image=self._photo, text="")

    def refresh_after_edit(self):
        """Re-render the current frame after crop/rotate/flip changes (paused UI)."""
        if self._last_raw_frame is None:
            return
        self._render_from_raw(self._last_raw_frame)

    def get_snapshot_image(self) -> Image.Image | None:
        """Current frame with edits applied (safe while playing via last-frame cache)."""
        if not self._state.loaded:
            return None
        if self._last_raw_frame is not None:
            return apply_pil_transforms(self._last_raw_frame.copy(), self._state)
        was_playing = self._engine is not None and self._engine.playing
        if self._engine and was_playing:
            self._engine.pause()
            self._btn_play.configure(text="\u25B6")
        try:
            raw = read_frame_at(self._state, self._state.current_frame)
            if raw is None:
                return None
            return apply_pil_transforms(raw, self._state)
        finally:
            if self._engine and was_playing:
                self._engine.play()
                self._btn_play.configure(text="\u23F8")

    def _update_time_display(self):
        if not self._state.loaded:
            return
        from services.ffmpeg_service import format_time
        cur = format_time(self._state.current_time)
        total = format_time(self._state.duration)
        self._time_label.configure(text=f"{cur} / {total}")

    def stop(self):
        self._polling = False
        self._last_raw_frame = None
        if self._engine:
            self._engine.stop()
            self._engine = None

    def clear(self):
        """Unload the current video: stop playback, blank the display, show placeholder."""
        self.stop()
        self._last_raw_frame = None
        self._time_label.configure(text="00:00.00 / 00:00.00")
        self._btn_play.configure(text="▶")
        # Cover the whole preview with the placeholder instead of doing
        # self._display.configure(image=None): configuring a CTkLabel's image to
        # None leaves a dangling Tk image reference, so the NEXT frame render
        # raises TclError('image "pyimageN" doesn\'t exist'), which crashes the
        # poll loop and leaves the reloaded video showing a permanent black
        # screen. Keeping the old CTkImage referenced avoids that; the next
        # attach_state() hides the placeholder and renders over it.
        self._placeholder.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._placeholder.lift()

    @property
    def engine(self) -> PlaybackEngine | None:
        return self._engine

    @property
    def is_playing(self) -> bool:
        return self._engine is not None and self._engine.playing
