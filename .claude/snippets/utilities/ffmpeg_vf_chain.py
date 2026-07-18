# From: services/edit_transforms.py:56
# Build -vf filter string, or None when no video transforms.

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
