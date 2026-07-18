# From: widgets/timeline.py:21

    def __init__(self, master, state: VideoState,
                 on_seek: Callable[[float], None] | None = None,
                 on_trim_change: Callable[[float, float], None] | None = None,
                 **kwargs):
        super().__init__(master, bg=COLORS["timeline_bg"],
                         height=TIMELINE_HEIGHT, **kwargs)
        self._state = state
        self._on_seek = on_seek
        self._on_trim_change = on_trim_change
        self._thumb_photos: list[ImageTk.PhotoImage] = []
        self._thumb_width = 0
        self._dragging: str | None = None  # "in", "out", or None

        # ── Canvas ───────────────────────────────────────────────
        self._canvas = tk.Canvas(
            self, bg=COLORS["timeline_bg"],
            height=TIMELINE_HEIGHT, highlightthickness=0,
            cursor="hand2",
        )
        self._canvas.pack(fill="both", expand=True)

        # Bind events
        self._canvas.bind("<Configure>", self._on_resize)
        self._canvas.bind("<ButtonPress-1>", self._on_press)
        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)

        # Track IDs
        self._thumb_ids: list[int] = []
        self._trim_rect_id: int | None = None
        self._handle_in_id: int | None = None
        self._handle_out_id: int | None = None
        self._playhead_id: int | None = None
        self._time_in_id: int | None = None
        self._time_out_id: int | None = None
