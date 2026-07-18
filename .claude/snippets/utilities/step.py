# From: services/video_service.py:256
# Step forward/back by delta frames.

    def step(self, delta: int = 1):
        """Step forward/back by delta frames."""
        self.pause()
        new_frame = self._state.current_frame + delta
        self.seek_frame(new_frame)
