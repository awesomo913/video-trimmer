# From: widgets/batch_panel.py:40

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLORS["bg"], **kwargs)

        self._folder: str = ""
        self._entries: list[BatchFileEntry] = []
        self._rows: dict[str, BatchFileRow] = {}
        self._job: BatchSplitJob | None = None
        self._scanning = False
        self._running = False

        self._build_ui()
