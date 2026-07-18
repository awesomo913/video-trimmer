# From: services/edit_transforms.py:33
# Apply crop / rotation / flip for preview and snapshot export.

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
