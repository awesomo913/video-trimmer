# From: app.py:215
# Called ~30fps during playback to update the timeline playhead.

    def _on_frame_update(self, frame_num: int):
        """Called ~30fps during playback to update the timeline playhead."""
        self._timeline.update_playhead(frame_num)
