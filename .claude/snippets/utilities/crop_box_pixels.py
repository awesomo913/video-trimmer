# From: services/edit_transforms.py:14
# Return (x, y, w, h) in source pixel coords, or None if crop disabled.

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
