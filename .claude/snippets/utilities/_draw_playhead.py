# From: widgets/timeline.py:196
# Draw the current position indicator as a white vertical line.

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
