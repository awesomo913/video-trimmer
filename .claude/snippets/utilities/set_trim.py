# From: widgets/timeline.py:275
# Programmatically set trim points.

    def set_trim(self, start: float, end: float):
        """Programmatically set trim points."""
        self._state.trim_start = max(0, start)
        self._state.trim_end = min(self._state.duration, end)
        self._draw_overlays()
