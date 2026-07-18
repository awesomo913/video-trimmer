# From: widgets/timeline.py:115
# Draw a semi-transparent overlay on the trimmed region.

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
