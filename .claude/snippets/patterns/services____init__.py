# From: services/video_service.py:153

    def __init__(self, state: VideoState, frame_queue: queue.Queue):
        self._state = state
        self._queue = frame_queue
        self._playing = False
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._speed = 1.0

        # Audio playback via ffplay subprocess — synced to video position
        self._audio_proc: subprocess.Popen | None = None
