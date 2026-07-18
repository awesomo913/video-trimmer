# From: widgets/video_preview.py:195
# Apply crop/rotate/flip from state, then scale to fit.

    def _render_from_raw(self, raw: Image.Image):
        """Apply crop/rotate/flip from state, then scale to fit."""
        edited = apply_pil_transforms(raw, self._state)
        dw = self._display.winfo_width()
        dh = self._display.winfo_height()
        if dw < 10 or dh < 10:
            dw, dh = 800, 450

        iw, ih = edited.size
        scale = min(dw / iw, dh / ih)
        new_w = max(1, int(iw * scale))
        new_h = max(1, int(ih * scale))

        resized = edited.resize((new_w, new_h), Image.LANCZOS)
        self._photo = ctk.CTkImage(
            light_image=resized, dark_image=resized, size=(new_w, new_h)
        )
        self._display.configure(image=self._photo, text="")
