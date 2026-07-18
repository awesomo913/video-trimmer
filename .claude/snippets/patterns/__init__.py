# From: app.py:32

    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(WINDOW_MIN_W, WINDOW_MIN_H)
        self.configure(fg_color=COLORS["bg"])

        # Try to set HiDPI awareness on Windows
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        # ── State ────────────────────────────────────────────────
        self._state = VideoState()
        self._mode = "single"
        self._batch_panel: BatchPanel | None = None

        # ── Layout ───────────────────────────────────────────────
        self._build_ui()
        self._bind_keys()

        # ── Drag and drop (via TkDnD if available) ───────────────
        self._setup_dnd()
