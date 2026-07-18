# From: app.py:152

    def _load_video(self, path: str):
        self._status.set_status("Loading...", COLORS["warning"])

        # Release previous
        self._preview.stop()
        self._state.release()

        try:
            self._state = open_video(path)
            meta = get_metadata(path)
        except Exception as exc:
            Toast(self, f"Failed to open: {exc}", "error")
            self._status.set_status("Ready")
            return

        # Wire up the new state
        self._preview.attach_state(self._state)
        self._timeline.attach_state(self._state)
        self._trim_ctrl._state = self._state
        self._trim_ctrl.update_display()
        self._edit_ctrl.attach_state(self._state)

        # Update toolbar metadata
        self._toolbar.set_metadata(
            f"{meta.resolution}  |  {meta.codec}  |  "
            f"{meta.fps} fps  |  {meta.duration_str}  |  {meta.size_str}"
        )

        # Status bar
        fname = os.path.basename(path)
        self._status.set_status(f"Loaded: {fname}", COLORS["success"])
        self._status.set_info(f"{meta.resolution} \u2022 {meta.size_str}")

        Toast(self, f"Opened {fname}", "success")
