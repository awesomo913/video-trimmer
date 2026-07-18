# From: widgets/split_config_panel.py:19

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLORS["bg_light"],
                         corner_radius=8, **kwargs)
        self._mode_var = ctk.StringVar(value="equal")
        self._n_var = ctk.IntVar(value=4)
        self._chunk_var = ctk.StringVar(value=str(SPLIT_DEFAULT_CHUNK_SECONDS))
        self._format_var = ctk.StringVar(value=list(EXPORT_FORMATS.keys())[0])
        self._quality_var = ctk.StringVar(value=list(QUALITY_PRESETS.keys())[0])
        self._audio_var = ctk.BooleanVar(value=True)
        self._preset_buttons: list[ctk.CTkButton] = []
        self._build_ui()
        self._refresh_mode_state()
