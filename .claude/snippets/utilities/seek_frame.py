# From: services/video_service.py:238
# Seek to a specific frame (works while paused or playing).

    def seek_frame(self, frame_num: int):
        """Seek to a specific frame (works while paused or playing)."""
        frame_num = max(0, min(frame_num, self._state.frame_count - 1))
        self._state.current_frame = frame_num
        # Restart audio from new position
        self._start_audio()
        if not self._playing:
            img = read_frame_at(self._state, frame_num)
            if img is not None:
                try:
                    self._queue.put_nowait(img)
                except queue.Full:
                    pass
