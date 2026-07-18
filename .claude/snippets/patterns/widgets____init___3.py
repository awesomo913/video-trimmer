# From: widgets/export_dialog.py:23

    def __init__(self, master, state: VideoState,
                 on_done: Callable[[str], None] | None = None,
                 on_error: Callable[[str], None] | None = None):
        super().__init__(master)
        self._state = state
        self._on_done = on_done
        self._on_error = on_error
        self._job: TrimJob | None = None

        self.title("Export Trimmed Video")
        self.geometry("480x460")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg"])
        self.transient(master)
        self.grab_set()

        self._build_ui()
        self.after(100, self.focus_force)
