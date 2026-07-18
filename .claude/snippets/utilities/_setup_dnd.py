# From: app.py:126
# Enable drag-and-drop via tkinterdnd2 if available, otherwise skip.

    def _setup_dnd(self):
        """Enable drag-and-drop via tkinterdnd2 if available, otherwise skip."""
        try:
            self.drop_target_register("DND_Files")
            self.dnd_bind("<<Drop>>", self._on_drop)
        except Exception:
            pass
