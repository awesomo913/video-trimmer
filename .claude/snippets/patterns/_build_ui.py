# From: app.py:62

    def _build_ui(self):
        # Mode switcher (very top)
        self._mode_switcher = ModeSwitcher(self, on_mode_change=self._on_mode_change)
        self._mode_switcher.pack(fill="x", side="top")

        # Toolbar
        self._toolbar = Toolbar(
            self,
            on_open=self._open_file,
            on_export=self._open_export,
            on_snapshot=self._export_snapshot,
        )
        self._toolbar.pack(fill="x", side="top")

        # Status bar
        self._status = StatusBar(self)
        self._status.pack(fill="x", side="bottom")

        # Trim controls
        self._trim_ctrl = TrimControls(
            self, state=self._state,
            on_set_in=self._set_trim_in,
            on_set_out=self._set_trim_out,
            on_trim_change=self._on_trim_change,
        )
        self._trim_ctrl.pack(fill="x", side="bottom")

        # Timeline
        self._timeline = Timeline(
            self, state=self._state,
            on_seek=self._on_timeline_seek,
            on_trim_change=self._on_trim_change,
        )
        self._timeline.pack(fill="x", side="bottom", ipady=4)

        self._edit_ctrl = EditControls(
            self,
            state=self._state,
            on_edit_change=self._on_edit_change,
        )
        self._edit_ctrl.pack(fill="x", side="bottom", padx=8, pady=(0, 4))

        # Video preview (takes remaining space)
        self._preview = VideoPreview(
            self, state=self._state,
            on_frame_update=self._on_frame_update,
        )
        self._preview.pack(fill="both", expand=True, side="top")
