# From: services/video_service.py:106
# Generate evenly-spaced thumbnail images in a background thread.

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
