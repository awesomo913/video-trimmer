"""Hand results from worker threads to the Tk main thread without touching Tk.

Worker threads call `post(fn, *args)`; the main thread drains the queue on a
timer. This keeps every widget call on the main thread, and it quietly stops
if the window has been destroyed (no stray TclError from a late worker).
"""

from __future__ import annotations

import logging
import queue
from collections.abc import Callable
from typing import Any

log = logging.getLogger(__name__)

POLL_MS = 40


class MainThreadDispatcher:
    """`schedule(ms, fn)` must be a main-thread timer such as `widget.after`."""

    def __init__(self, schedule: Callable[[int, Callable[[], None]], Any],
                 alive: Callable[[], bool] = lambda: True):
        self._schedule = schedule
        self._alive = alive
        self._queue: queue.SimpleQueue[tuple[Callable[..., None], tuple]] = queue.SimpleQueue()
        self._closed = False

    def start(self) -> None:
        """Begin polling. Call from the main thread."""
        self._tick()

    def close(self) -> None:
        self._closed = True

    def post(self, fn: Callable[..., None], *args: Any) -> None:
        """Thread-safe. `fn(*args)` will run later on the main thread."""
        if not self._closed:
            self._queue.put((fn, args))

    def drain(self) -> int:
        """Run everything queued so far. Returns how many callbacks ran."""
        ran = 0
        while True:
            try:
                fn, args = self._queue.get_nowait()
            except queue.Empty:
                return ran
            try:
                fn(*args)
            except Exception:
                # A broken UI callback must not kill the poll loop for the rest.
                log.exception("UI callback %r failed", fn)
            ran += 1

    def _tick(self) -> None:
        if self._closed:
            return
        if not self._alive():
            self._closed = True
            return
        self.drain()
        self._schedule(POLL_MS, self._tick)
