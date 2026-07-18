# From: widgets/trim_controls.py:154
# Refresh the timecode entries and duration from current state.

    def update_display(self):
        """Refresh the timecode entries and duration from current state."""
        self._in_entry.delete(0, "end")
        self._in_entry.insert(0, format_time(self._state.trim_start))

        self._out_entry.delete(0, "end")
        self._out_entry.insert(0, format_time(self._state.trim_end))

        dur = max(0, self._state.trim_end - self._state.trim_start)
        self._dur_label.configure(text=format_time(dur))
