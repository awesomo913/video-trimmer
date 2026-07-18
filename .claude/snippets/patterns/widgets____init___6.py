# From: widgets/status_bar.py:13

    def __init__(self, master, **kwargs):
        super().__init__(master, height=28, fg_color=COLORS["bg_light"], **kwargs)
        self.pack_propagate(False)

        self._status = ctk.CTkLabel(
            self, text="Ready", font=FONT_UI_SMALL,
            text_color=COLORS["text_dim"], anchor="w",
        )
        self._status.pack(side="left", padx=10)

        self._info = ctk.CTkLabel(
            self, text="", font=FONT_MONO_SMALL,
            text_color=COLORS["text_dim"], anchor="e",
        )
        self._info.pack(side="right", padx=10)
