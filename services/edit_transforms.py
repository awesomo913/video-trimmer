"""Preview + FFmpeg helpers for crop, rotate, flip."""

from __future__ import annotations

from PIL import Image, ImageOps

from services.video_service import VideoState


def _clamp_pct(v: float) -> float:
    return max(0.0, min(50.0, float(v)))


def crop_box_pixels(state: VideoState) -> tuple[int, int, int, int] | None:
    """Return (x, y, w, h) in source pixel coords, or None if crop disabled."""
    if not state.crop_enabled or state.width <= 0 or state.height <= 0:
        return None
    l = _clamp_pct(state.crop_left_pct)
    t = _clamp_pct(state.crop_top_pct)
    r = _clamp_pct(state.crop_right_pct)
    b = _clamp_pct(state.crop_bottom_pct)
    x = int(state.width * l / 100.0)
    y = int(state.height * t / 100.0)
    w = state.width - x - int(state.width * r / 100.0)
    h = state.height - y - int(state.height * b / 100.0)
    w = max(2, min(w, state.width - x))
    h = max(2, min(h, state.height - y))
    if w < 2 or h < 2:
        return None
    return x, y, w, h


def apply_pil_transforms(img: Image.Image, state: VideoState) -> Image.Image:
    """Apply crop / rotation / flip for preview and snapshot export."""
    out = img
    box = crop_box_pixels(state)
    if box is not None:
        x, y, w, h = box
        out = out.crop((x, y, x + w, y + h))

    rot = state.rotation_cw % 360
    if rot == 90:
        out = out.transpose(Image.ROTATE_270)
    elif rot == 180:
        out = out.transpose(Image.ROTATE_180)
    elif rot == 270:
        out = out.transpose(Image.ROTATE_90)

    if state.flip_horizontal:
        out = ImageOps.mirror(out)
    if state.flip_vertical:
        out = ImageOps.flip(out)
    return out


def ffmpeg_vf_chain(state: VideoState) -> str | None:
    """Build -vf filter string, or None when no video transforms."""
    parts: list[str] = []
    box = crop_box_pixels(state)
    if box is not None:
        x, y, w, h = box
        parts.append(f"crop={w}:{h}:{x}:{y}")

    rot = state.rotation_cw % 360
    if rot == 90:
        parts.append("transpose=1")
    elif rot == 180:
        parts.append("transpose=1,transpose=1")
    elif rot == 270:
        parts.append("transpose=2")

    if state.flip_horizontal:
        parts.append("hflip")
    if state.flip_vertical:
        parts.append("vflip")

    if not parts:
        return None
    return ",".join(parts)


def edits_active(state: VideoState) -> bool:
    return ffmpeg_vf_chain(state) is not None
