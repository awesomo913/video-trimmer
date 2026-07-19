"""OpenCV-based video operations — frame extraction, thumbnails, playback state."""

from __future__ import annotations

import logging
import queue
import subprocess
import threading
from dataclasses import dataclass, field
from typing import Callable

import cv2
from PIL import Image

from config import THUMBNAIL_COUNT, THUMBNAIL_HEIGHT, FFPLAY_BIN

log = logging.getLogger(__name__)


@dataclass
class VideoState:
    """Shared mutable state for the currently loaded video."""
    path: str = ""
    cap: cv2.VideoCapture | None = field(default=None, repr=False)
    frame_count: int = 0
    fps: float = 0.0
    width: int = 0
    height: int = 0
    duration: float = 0.0
    current_frame: int = 0

    # Trim points (in seconds)
    trim_start: float = 0.0
    trim_end: float = 0.0

    # Edit transforms (preview + export): crop = inset % per edge (0–50)
    crop_enabled: bool = False
    crop_left_pct: float = 0.0
    crop_top_pct: float = 0.0
    crop_right_pct: float = 0.0
    crop_bottom_pct: float = 0.0
    rotation_cw: int = 0  # 0, 90, 180, 270 clockwise
    flip_horizontal: bool = False
    flip_vertical: bool = False

    @property
    def current_time(self) -> float:
        if self.fps <= 0:
            return 0.0
        return self.current_frame / self.fps

    @property
    def loaded(self) -> bool:
        return self.cap is not None and self.cap.isOpened()

    def time_to_frame(self, t: float) -> int:
        return max(0, min(int(t * self.fps), self.frame_count - 1))

    def frame_to_time(self, f: int) -> float:
        if self.fps <= 0:
            return 0.0
        return f / self.fps

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None


def open_video(path: str) -> VideoState:
    """Open a video file and return populated VideoState."""
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {path}")

    fc = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    dur = fc / fps if fps > 0 else 0.0

    return VideoState(
        path=path, cap=cap,
        frame_count=fc, fps=fps,
        width=w, height=h, duration=dur,
        trim_start=0.0, trim_end=dur,
    )


def read_frame_at(state: VideoState, frame_num: int) -> Image.Image | None:
    """Seek to a specific frame and return it as a PIL Image."""
    if not state.loaded:
        return None
    state.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
    ret, frame = state.cap.read()
    if not ret:
        return None
    state.current_frame = frame_num
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def read_frame_at_time(state: VideoState, time_sec: float) -> Image.Image | None:
    """Seek to a specific time and return the frame."""
    frame_num = state.time_to_frame(time_sec)
    return read_frame_at(state, frame_num)


def generate_thumbnails(
    state: VideoState,
    count: int = THUMBNAIL_COUNT,
    height: int = THUMBNAIL_HEIGHT,
    on_done: Callable[[list[Image.Image]], None] | None = None,
) -> None:
    """Generate evenly-spaced thumbnail images in a background thread."""
    def _worker():
        thumbs: list[Image.Image] = []
        if not state.loaded or state.frame_count < 2:
            if on_done:
                on_done(thumbs)
            return

        # Use a separate capture so we don't interfere with playback
        cap = cv2.VideoCapture(state.path)
        if not cap.isOpened():
            if on_done:
                on_done(thumbs)
            return

        step = max(1, state.frame_count // count)
        aspect = state.width / max(state.height, 1)
        thumb_w = int(height * aspect)

        try:
            for i in range(count):
                frame_num = min(i * step, state.frame_count - 1)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                if not ret:
                    # Pad with a black frame
                    thumbs.append(Image.new("RGB", (thumb_w, height), (20, 20, 30)))
                    continue
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb).resize((thumb_w, height), Image.LANCZOS)
                thumbs.append(img)
        finally:
            cap.release()  # never leak the OS video handle, even on decode error
        if on_done:
            on_done(thumbs)

    threading.Thread(target=_worker, daemon=True).start()


class PlaybackEngine:
    """Threaded playback engine — pushes frames to a queue for the UI to consume."""

    def __init__(self, state: VideoState, frame_queue: queue.Queue):
        self._state = state
        self._queue = frame_queue
        self._playing = False
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._speed = 1.0
        self._loop = False  # when False, playback halts at trim_end instead of repeating

        # Audio playback via ffplay subprocess — synced to video position
        self._audio_proc: subprocess.Popen | None = None

    @property
    def playing(self) -> bool:
        return self._playing

    @property
    def loop(self) -> bool:
        return self._loop

    @loop.setter
    def loop(self, val: bool):
        self._loop = bool(val)

    @property
    def speed(self) -> float:
        return self._speed

    @speed.setter
    def speed(self, val: float):
        prev = self._speed
        self._speed = max(0.25, min(val, 4.0))
        # Audio only plays at 1x — kill ffplay when speed leaves 1x
        if prev == 1.0 and self._speed != 1.0:
            self._kill_audio()
        elif prev != 1.0 and self._speed == 1.0 and self._playing:
            self._start_audio()

    # ── Audio helpers (ffplay subprocess) ──────────────────────

    def _start_audio(self):
        """Spawn ffplay for the current trim region's audio at the current position."""
        if self._speed != 1.0 or not self._state.path:
            return
        self._kill_audio()
        seek = max(0.0, self._state.current_time)
        cmd = [FFPLAY_BIN, "-nodisp", "-autoexit", "-ss", str(seek)]
        # Bound audio to the trim-out point so it stops with the video; it is
        # restarted from trim_start each time the video loops (see _run).
        dur = self._state.trim_end - seek
        if dur > 0:
            cmd += ["-t", str(dur)]
        cmd.append(self._state.path)
        try:
            self._audio_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception as exc:
            self._audio_proc = None
            log.warning("ffplay failed to start (audio disabled): %s", exc)

    def _kill_audio(self):
        if self._audio_proc is None:
            return
        try:
            self._audio_proc.kill()
            self._audio_proc.wait(timeout=1)
        except Exception as exc:
            log.warning("failed to kill ffplay: %s", exc)
            # Only drop the handle if the process is actually gone, else we'd
            # orphan a still-playing ffplay we can never stop again.
            if self._audio_proc.poll() is None:
                return
        self._audio_proc = None

    # ── Playback control ─────────────────────────────────────

    def play(self):
        if self._playing or not self._state.loaded:
            return
        # Parked at (or past) the trim-out point with looping off — rewind to
        # trim-in so pressing Play replays the clip instead of instantly halting.
        # Compare by FRAME, not float time: trim_end defaults to duration
        # (frame_count/fps) while the last decodable frame sits at
        # (frame_count-1)/fps, so a float compare is always one frame short and
        # the rewind would never fire on the common end-of-file path.
        if not self._loop and self._state.current_frame >= self._state.time_to_frame(self._state.trim_end):
            self._state.current_frame = self._state.time_to_frame(self._state.trim_start)
        self._start_audio()
        self._playing = True
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def pause(self):
        self._playing = False
        self._stop.set()
        self._kill_audio()

    def toggle(self):
        if self._playing:
            self.pause()
        else:
            self.play()

    def seek_frame(self, frame_num: int):
        """Seek to a specific frame (works while paused or playing)."""
        frame_num = max(0, min(frame_num, self._state.frame_count - 1))
        self._state.current_frame = frame_num
        # Restart audio from new position — only while actually playing, so
        # scrubbing the timeline while paused doesn't blast audio.
        if self._playing:
            self._start_audio()
        if not self._playing:
            img = read_frame_at(self._state, frame_num)
            if img is not None:
                try:
                    self._queue.put_nowait(img)
                except queue.Full:
                    pass

    def seek_time(self, time_sec: float):
        frame = self._state.time_to_frame(time_sec)
        self.seek_frame(frame)

    def step(self, delta: int = 1):
        """Step forward/back by delta frames."""
        self.pause()
        new_frame = self._state.current_frame + delta
        self.seek_frame(new_frame)

    def stop(self):
        self._playing = False
        self._stop.set()
        self._kill_audio()
        # Wait for the playback thread to finish its in-flight cap.read() before
        # the caller releases the capture — avoids a cross-thread use of the
        # (non-thread-safe) OpenCV handle on file switch / close.
        t = self._thread
        if t is not None and t is not threading.current_thread():
            t.join(timeout=1)
        self._thread = None

    def _finish_playback(self):
        """Halt at the trim-out point (looping off) — stop audio, clear the flag."""
        self._playing = False
        self._kill_audio()

    def _run(self):
        cap = self._state.cap
        if cap is None:
            return
        cap.set(cv2.CAP_PROP_POS_FRAMES, self._state.current_frame)

        import time
        frame_delay = 1.0 / (self._state.fps * self._speed) if self._state.fps > 0 else 0.033

        while not self._stop.is_set():
            ret, frame = cap.read()
            if not ret:
                # End of file: loop back to trim_start, or stop if looping is off
                if not self._loop:
                    # Park on the trim-out frame so play() sees us at the end and
                    # rewinds on the next press (EOF leaves current_frame one short).
                    self._state.current_frame = self._state.time_to_frame(self._state.trim_end)
                    self._finish_playback()
                    break
                self._state.current_frame = self._state.time_to_frame(self._state.trim_start)
                cap.set(cv2.CAP_PROP_POS_FRAMES, self._state.current_frame)
                self._start_audio()
                continue

            self._state.current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1

            # Reached trim end: loop back to trim_start, or stop if looping is off
            if self._state.current_time >= self._state.trim_end:
                if not self._loop:
                    self._state.current_frame = self._state.time_to_frame(self._state.trim_end)
                    self._finish_playback()
                    break
                self._state.current_frame = self._state.time_to_frame(self._state.trim_start)
                cap.set(cv2.CAP_PROP_POS_FRAMES, self._state.current_frame)
                self._start_audio()
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            try:
                self._queue.put(img, timeout=0.1)
            except queue.Full:
                pass

            # Recalculate delay in case speed changed
            frame_delay = 1.0 / (self._state.fps * self._speed) if self._state.fps > 0 else 0.033
            time.sleep(frame_delay)

        # No trailing `self._playing = False` here: every exit path already clears
        # it (pause/stop/_finish_playback). Re-clearing it after the loop could
        # stomp a _playing=True set by a replay thread that started in the gap,
        # leaving two threads on the non-thread-safe VideoCapture.
