# From: widgets/split_config_panel.py:226
# Lock the whole panel during a running batch.

    def set_enabled(self, enabled: bool) -> None:
        """Lock the whole panel during a running batch."""
        state = "normal" if enabled else "disabled"
        for child in self.winfo_children():
            self._set_subtree_state(child, state)
        if enabled:
            self._refresh_mode_state()
