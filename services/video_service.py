"""OpenCV-based video operations — frame extraction, thumbnails, playback state."""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass, field
from typing import Callable

import cv2
from PIL import Image

from config import THUMBNAIL_COUNT, THUMBNAIL_HEIGHT


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

        cap.release()
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

    @property
    def playing(self) -> bool:
        return self._playing

    @property
    def speed(self) -> float:
        return self._speed

    @speed.setter
    def speed(self, val: float):
        self._speed = max(0.25, min(val, 4.0))

    def play(self):
        if self._playing or not self._state.loaded:
            return
        self._playing = True
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def pause(self):
        self._playing = False
        self._stop.set()

    def toggle(self):
        if self._playing:
            self.pause()
        else:
            self.play()

    def seek_frame(self, frame_num: int):
        """Seek to a specific frame (works while paused or playing)."""
        frame_num = max(0, min(frame_num, self._state.frame_count - 1))
        self._state.current_frame = frame_num
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
                # End of video — loop back to trim_start
                self._state.current_frame = self._state.time_to_frame(self._state.trim_start)
                cap.set(cv2.CAP_PROP_POS_FRAMES, self._state.current_frame)
                continue

            self._state.current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1

            # Stop at trim end
            if self._state.current_time >= self._state.trim_end:
                self._state.current_frame = self._state.time_to_frame(self._state.trim_start)
                cap.set(cv2.CAP_PROP_POS_FRAMES, self._state.current_frame)
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

        self._playing = False
