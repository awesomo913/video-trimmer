# From: widgets/timeline.py:97
# Draw trim region, handles, and playhead.

    def _draw_overlays(self):
        """Draw trim region, handles, and playhead."""
        self._draw_trim_region()
        self._draw_handles()
        self._draw_playhead()
