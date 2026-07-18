# From: services/video_service.py:184
# Spawn ffplay -nodisp -autoexit at current video position.

    def _start_audio(self):
        """Spawn ffplay -nodisp -autoexit at current video position."""
        if self._speed != 1.0 or not self._state.path:
            return
        self._kill_audio()
        seek = max(0.0, self._state.current_time)
        cmd = [
            FFPLAY_BIN,
            "-nodisp", "-autoexit",
            "-ss", str(seek),
            self._state.path,
        ]
        try:
            self._audio_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception:
            self._audio_proc = None
