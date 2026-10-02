"""Small filesystem helpers for output naming and overwrite safety."""

from __future__ import annotations

import os


def same_file(a: str, b: str) -> bool:
    """True if two paths point at the same file (case-insensitive on Windows, follows links)."""
    try:
        if os.path.exists(a) and os.path.exists(b):
            return os.path.samefile(a, b)
    except OSError:
        pass
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def unique_path(path: str) -> str:
    """Return `path`, or `name (2).ext`, `name (3).ext`... if it already exists."""
    if not os.path.exists(path):
        return path
    root, ext = os.path.splitext(path)
    n = 2
    while os.path.exists(f"{root} ({n}){ext}"):
        n += 1
    return f"{root} ({n}){ext}"
