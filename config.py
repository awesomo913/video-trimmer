"""App-wide constants: colors, fonts, paths, supported formats."""

import os
import shutil

APP_NAME = "Video Trimmer"
APP_VERSION = "1.0.0"

# ── Theme ──────────────────────────────────────────────────────────
COLORS = {
    "bg":          "#1a1a2e",
    "bg_light":    "#16213e",
    "bg_surface":  "#0f3460",
    "accent":      "#e94560",
    "success":     "#4ecca3",
    "warning":     "#f0a500",
    "error":       "#e94560",
    "text":        "#eaeaea",
    "text_dim":    "#8892a0",
    "handle_in":   "#4ecca3",
    "handle_out":  "#e94560",
    "playhead":    "#ffffff",
    "timeline_bg": "#111827",
    "trim_region": "#4ecca340",
}

FONT_UI = ("Segoe UI", 11)
FONT_UI_SMALL = ("Segoe UI", 10)
FONT_UI_BOLD = ("Segoe UI", 11, "bold")
FONT_MONO = ("Consolas", 11)
FONT_MONO_SMALL = ("Consolas", 10)
FONT_TITLE = ("Segoe UI", 14, "bold")

# ── FFmpeg ─────────────────────────────────────────────────────────
_BUNDLED_FFMPEG_DIR = os.path.join(
    os.path.dirname(__file__), "..", "ffmpeg",
    "ffmpeg-8.1-essentials_build", "bin",
)

def _find_binary(name: str) -> str:
    bundled = os.path.join(_BUNDLED_FFMPEG_DIR, f"{name}.exe")
    if os.path.isfile(bundled):
        return bundled
    found = shutil.which(name)
    if found:
        return found
    return name  # hope it's on PATH at runtime

FFMPEG_BIN = _find_binary("ffmpeg")
FFPROBE_BIN = _find_binary("ffprobe")

# ── Supported formats ─────────────────────────────────────────────
VIDEO_EXTENSIONS = (
    ".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv",
    ".wmv", ".ts", ".m4v", ".mpg", ".mpeg", ".3gp",
    ".m2ts", ".vob", ".ogv",
)

EXPORT_FORMATS = {
    "MP4  (.mp4)":  {"ext": ".mp4",  "container": "mp4"},
    "MKV  (.mkv)":  {"ext": ".mkv",  "container": "matroska"},
    "AVI  (.avi)":  {"ext": ".avi",  "container": "avi"},
    "WebM (.webm)": {"ext": ".webm", "container": "webm"},
    "MOV  (.mov)":  {"ext": ".mov",  "container": "mov"},
}

QUALITY_PRESETS = {
    "Copy (fastest, lossless)": {"crf": None, "copy": True},
    "High (CRF 18)":           {"crf": 18,   "copy": False},
    "Medium (CRF 23)":         {"crf": 23,   "copy": False},
    "Low (CRF 28)":            {"crf": 28,   "copy": False},
    "Compact (CRF 35)":        {"crf": 35,   "copy": False},
}

# ── Window defaults ───────────────────────────────────────────────
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
WINDOW_MIN_W = 900
WINDOW_MIN_H = 600

THUMBNAIL_COUNT = 24
THUMBNAIL_HEIGHT = 54
TIMELINE_HEIGHT = 80
