# From: widgets/timeline.py:147
# Draw the in/out trim handles as colored rectangles with grip lines.

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
