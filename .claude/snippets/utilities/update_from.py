# From: widgets/batch_file_row.py:84
# Re-render after status/progress change.

    def update_from(self, entry: BatchFileEntry) -> None:
        """Re-render after status/progress change."""
        self._entry = entry
        status = entry.status
        if status == STATUS_PENDING and entry.meta_error:
            status = STATUS_UNREADABLE

        self._status_label.configure(
            text=_STATUS_TEXT.get(status, status),
            text_color=_STATUS_COLORS.get(status, COLORS["text"]),
        )

        if status == STATUS_RUNNING:
            self._progress.set(entry.progress / 100.0)
            if not self._progress_packed:
                self._progress.pack(side="right", padx=10)
                self._progress_packed = True
        else:
            if self._progress_packed:
                self._progress.pack_forget()
                self._progress_packed = False
