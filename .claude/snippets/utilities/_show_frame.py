# From: widgets/video_preview.py:190
# Remember raw pixels, apply edits, scale to the label, and show.

    def _show_frame(self, img: Image.Image):
        """Remember raw pixels, apply edits, scale to the label, and show."""
        self._last_raw_frame = img.copy()
        self._render_from_raw(self._last_raw_frame)
