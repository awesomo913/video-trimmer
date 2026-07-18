# From: widgets/timeline.py:57
# Load a new video — regenerate thumbnails and reset handles.

    def attach_state(self, state: VideoState):
        """Load a new video — regenerate thumbnails and reset handles."""
        self._state = state
        self._canvas.delete("all")
        self._thumb_photos.clear()
        self._thumb_ids.clear()
        self._generate_thumbs()
