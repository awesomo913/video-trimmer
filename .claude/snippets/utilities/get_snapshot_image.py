# From: widgets/video_preview.py:220
# Current frame with edits applied (safe while playing via last-frame cache).

    def get_snapshot_image(self) -> Image.Image | None:
        """Current frame with edits applied (safe while playing via last-frame cache)."""
        if not self._state.loaded:
            return None
        if self._last_raw_frame is not None:
            return apply_pil_transforms(self._last_raw_frame.copy(), self._state)
        was_playing = self._engine is not None and self._engine.playing
        if self._engine and was_playing:
            self._engine.pause()
            self._btn_play.configure(text="\u25B6")
        try:
            raw = read_frame_at(self._state, self._state.current_frame)
            if raw is None:
                return None
            return apply_pil_transforms(raw, self._state)
        finally:
            if self._engine and was_playing:
                self._engine.play()
                self._btn_play.configure(text="\u23F8")
