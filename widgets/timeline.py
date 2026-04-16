"""Timeline widget — thumbnail strip with draggable trim handles and playhead."""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from PIL import Image, ImageTk

from config import COLORS, TIMELINE_HEIGHT, THUMBNAIL_HEIGHT, FONT_MONO_SMALL
from services.video_service import VideoState, generate_thumbnails


class Timeline(tk.Frame):
    """Canvas-based timeline with thumbnail strip, trim handles, and playhead."""

    HANDLE_WIDTH = 12
    HANDLE_COLOR_IN = COLORS["handle_in"]
    HANDLE_COLOR_OUT = COLORS["handle_out"]

    def __init__(self, master, state: VideoState,
                 on_seek: Callable[[float], None] | None = None,
                 on_trim_change: Callable[[float, float], None] | None = None,
                 **kwargs):
        super().__init__(master, bg=COLORS["timeline_bg"],
                         height=TIMELINE_HEIGHT, **kwargs)
        self._state = state
        self._on_seek = on_seek
        self._on_trim_change = on_trim_change
        self._thumb_photos: list[ImageTk.PhotoImage] = []
        self._thumb_width = 0
        self._dragging: str | None = None  # "in", "out", or None

        # ── Canvas ───────────────────────────────────────────────
        self._canvas = tk.Canvas(
            self, bg=COLORS["timeline_bg"],
            height=TIMELINE_HEIGHT, highlightthickness=0,
            cursor="hand2",
        )
        self._canvas.pack(fill="both", expand=True)

        # Bind events
        self._canvas.bind("<Configure>", self._on_resize)
        self._canvas.bind("<ButtonPress-1>", self._on_press)
        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)

        # Track IDs
        self._thumb_ids: list[int] = []
        self._trim_rect_id: int | None = None
        self._handle_in_id: int | None = None
        self._handle_out_id: int | None = None
        self._playhead_id: int | None = None
        self._time_in_id: int | None = None
        self._time_out_id: int | None = None

    def attach_state(self, state: VideoState):
        """Load a new video — regenerate thumbnails and reset handles."""
        self._state = state
        self._canvas.delete("all")
        self._thumb_photos.clear()
        self._thumb_ids.clear()
        self._generate_thumbs()

    def _generate_thumbs(self):
        generate_thumbnails(
            self._state,
            on_done=lambda thumbs: self._canvas.after(0, self._on_thumbs_ready, thumbs),
        )

    def _on_thumbs_ready(self, thumbs: list[Image.Image]):
        if not thumbs:
            return
        self._canvas.delete("all")
        self._thumb_photos.clear()
        self._thumb_ids.clear()

        cw = self._canvas.winfo_width()
        if cw < 10:
            cw = 800

        n = len(thumbs)
        self._thumb_width = cw / n

        # Draw thumbnails
        for i, img in enumerate(thumbs):
            tw = max(1, int(self._thumb_width))
            resized = img.resize((tw, THUMBNAIL_HEIGHT), Image.LANCZOS)
            photo = ImageTk.PhotoImage(resized)
            self._thumb_photos.append(photo)
            x = int(i * self._thumb_width)
            tid = self._canvas.create_image(x, 2, image=photo, anchor="nw")
            self._thumb_ids.append(tid)

        self._draw_overlays()

    def _draw_overlays(self):
        """Draw trim region, handles, and playhead."""
        self._draw_trim_region()
        self._draw_handles()
        self._draw_playhead()

    def _time_to_x(self, t: float) -> float:
        cw = self._canvas.winfo_width()
        if self._state.duration <= 0:
            return 0
        return (t / self._state.duration) * cw

    def _x_to_time(self, x: float) -> float:
        cw = self._canvas.winfo_width()
        if cw <= 0:
            return 0
        return max(0, min((x / cw) * self._state.duration, self._state.duration))

    def _draw_trim_region(self):
        """Draw a semi-transparent overlay on the trimmed region."""
        if self._trim_rect_id is not None:
            self._canvas.delete(self._trim_rect_id)

        cw = self._canvas.winfo_width()
        ch = TIMELINE_HEIGHT

        # Dim outside the trim region
        x_in = self._time_to_x(self._state.trim_start)
        x_out = self._time_to_x(self._state.trim_end)

        # Left dim region
        self._canvas.delete("dim_left", "dim_right")
        self._canvas.create_rectangle(
            0, 0, x_in, ch,
            fill="#000000", stipple="gray50",
            outline="", tags="dim_left",
        )
        # Right dim region
        self._canvas.create_rectangle(
            x_out, 0, cw, ch,
            fill="#000000", stipple="gray50",
            outline="", tags="dim_right",
        )

        # Trim region border
        self._trim_rect_id = self._canvas.create_rectangle(
            x_in, 0, x_out, ch,
            outline=COLORS["accent"], width=2,
        )

    def _draw_handles(self):
        """Draw the in/out trim handles as colored rectangles with grip lines."""
        ch = TIMELINE_HEIGHT
        hw = self.HANDLE_WIDTH

        # Remove old handles
        self._canvas.delete("handle_in", "handle_out", "time_label")

        x_in = self._time_to_x(self._state.trim_start)
        x_out = self._time_to_x(self._state.trim_end)

        # In handle (green)
        self._handle_in_id = self._canvas.create_rectangle(
            x_in - hw, 0, x_in, ch,
            fill=self.HANDLE_COLOR_IN, outline="",
            tags="handle_in",
        )
        # Grip lines
        for dy in range(ch // 4, ch - ch // 4, 6):
            self._canvas.create_line(
                x_in - hw + 3, dy, x_in - 3, dy,
                fill="#aaaaaa", tags="handle_in",
            )

        # Out handle (red)
        self._handle_out_id = self._canvas.create_rectangle(
            x_out, 0, x_out + hw, ch,
            fill=self.HANDLE_COLOR_OUT, outline="",
            tags="handle_out",
        )
        for dy in range(ch // 4, ch - ch // 4, 6):
            self._canvas.create_line(
                x_out + 3, dy, x_out + hw - 3, dy,
                fill="#aaaaaa", tags="handle_out",
            )

        # Time labels above handles
        from services.ffmpeg_service import format_time
        self._canvas.create_text(
            x_in, ch - 4, text=format_time(self._state.trim_start),
            fill=self.HANDLE_COLOR_IN, font=FONT_MONO_SMALL,
            anchor="sw", tags="time_label",
        )
        self._canvas.create_text(
            x_out, ch - 4, text=format_time(self._state.trim_end),
            fill=self.HANDLE_COLOR_OUT, font=FONT_MONO_SMALL,
            anchor="se", tags="time_label",
        )

    def _draw_playhead(self):
        """Draw the current position indicator as a white vertical line."""
        self._canvas.delete("playhead")
        if not self._state.loaded:
            return
        x = self._time_to_x(self._state.current_time)
        ch = TIMELINE_HEIGHT
        self._playhead_id = self._canvas.create_line(
            x, 0, x, ch,
            fill=COLORS["playhead"], width=2,
            tags="playhead",
        )
        # Small triangle at top
        self._canvas.create_polygon(
            x - 5, 0, x + 5, 0, x, 8,
            fill=COLORS["playhead"], outline="",
            tags="playhead",
        )

    def update_playhead(self, frame_num: int):
        """Called by the app to update playhead position during playback."""
        if not self._state.loaded:
            return
        self._draw_playhead()

    # ── Mouse interaction ────────────────────────────────────────

    def _hit_handle(self, x: float) -> str | None:
        hw = self.HANDLE_WIDTH
        x_in = self._time_to_x(self._state.trim_start)
        x_out = self._time_to_x(self._state.trim_end)
        if x_in - hw <= x <= x_in + 4:
            return "in"
        if x_out - 4 <= x <= x_out + hw:
            return "out"
        return None

    def _on_press(self, event: tk.Event):
        handle = self._hit_handle(event.x)
        if handle:
            self._dragging = handle
            self._canvas.configure(cursor="sb_h_double_arrow")
            return

        # Click on timeline = seek
        t = self._x_to_time(event.x)
        if self._on_seek:
            self._on_seek(t)

    def _on_drag(self, event: tk.Event):
        if self._dragging is None:
            return

        t = self._x_to_time(event.x)

        if self._dragging == "in":
            t = max(0, min(t, self._state.trim_end - 0.1))
            self._state.trim_start = t
        elif self._dragging == "out":
            t = max(self._state.trim_start + 0.1, min(t, self._state.duration))
            self._state.trim_end = t

        self._draw_trim_region()
        self._draw_handles()
        self._draw_playhead()

        if self._on_trim_change:
            self._on_trim_change(self._state.trim_start, self._state.trim_end)

    def _on_release(self, event: tk.Event):
        self._dragging = None
        self._canvas.configure(cursor="hand2")

    def _on_resize(self, event: tk.Event):
        if self._state.loaded and self._thumb_photos:
            self._draw_overlays()
        elif self._state.loaded:
            self._generate_thumbs()

    def set_trim(self, start: float, end: float):
        """Programmatically set trim points."""
        self._state.trim_start = max(0, start)
        self._state.trim_end = min(self._state.duration, end)
        self._draw_overlays()
