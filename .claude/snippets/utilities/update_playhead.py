# From: widgets/timeline.py:215
# Called by the app to update playhead position during playback.

    def update_playhead(self, frame_num: int):
        """Called by the app to update playhead position during playback."""
        if not self._state.loaded:
            return
        self._draw_playhead()
