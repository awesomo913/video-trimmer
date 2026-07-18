# From: app.py:235
# Called when trim handles are dragged or timecodes are entered.

    def _on_trim_change(self, start: float, end: float):
        """Called when trim handles are dragged or timecodes are entered."""
        self._trim_ctrl.update_display()
        self._timeline._draw_overlays()
