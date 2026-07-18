# From: widgets/video_preview.py:214
# Re-render the current frame after crop/rotate/flip changes (paused UI).

    def refresh_after_edit(self):
        """Re-render the current frame after crop/rotate/flip changes (paused UI)."""
        if self._last_raw_frame is None:
            return
        self._render_from_raw(self._last_raw_frame)
