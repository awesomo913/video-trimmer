# From: widgets/video_preview.py:108
# Attach a new video state after opening a file.

    def attach_state(self, state: VideoState):
        """Attach a new video state after opening a file."""
        self.stop()
        self._state = state
        self._last_raw_frame = None
        self._frame_queue = queue.Queue(maxsize=3)
        self._engine = PlaybackEngine(state, self._frame_queue)
        self._placeholder.place_forget()
        self._start_polling()
        # Show first frame
        self._engine.seek_frame(0)
        self._update_time_display()
