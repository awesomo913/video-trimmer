# From: widgets/split_config_panel.py:165
# Visually grey out the inactive group.

    def _refresh_mode_state(self) -> None:
        """Visually grey out the inactive group."""
        equal_active = self._mode_var.get() == "equal"
        for child in self._equal_frame.winfo_children():
            self._set_subtree_state(child, "normal" if equal_active else "disabled")
        for child in self._duration_frame.winfo_children():
            self._set_subtree_state(child, "disabled" if equal_active else "normal")
