# From: services/batch_split_service.py:87
# Find every video in `path`, probe metadata, return sorted entries.

def scan_folder(path: str) -> list[BatchFileEntry]:
    """Find every video in `path`, probe metadata, return sorted entries.

    Corrupt or unreadable files become entries with `status=UNREADABLE`
    and a `meta_error` message — they don't abort the scan.

    Raises ScanError if the folder itself cannot be opened (caller distinguishes
    "empty folder" from "unreadable folder").
    """
    entries: list[BatchFileEntry] = []
    if not os.path.isdir(path):
        raise ScanError(f"Not a folder: {path}")

    try:
        items = list(os.scandir(path))
    except OSError as exc:
        raise ScanError(f"Cannot read folder ({exc.__class__.__name__}): {exc}") from exc

    for item in items:
        if not item.is_file():
            continue
        ext = os.path.splitext(item.name)[1].lower()
        if ext not in VIDEO_EXTENSIONS:
            continue

        entry = BatchFileEntry(path=item.path)
        try:
            meta = get_metadata(item.path)
            entry.duration = meta.duration
            if entry.duration <= 0:
                entry.meta_error = "zero or unknown duration"
                entry.status = STATUS_UNREADABLE
        except Exception as exc:
            entry.meta_error = str(exc)[:200]
            entry.status = STATUS_UNREADABLE
        entries.append(entry)

    entries.sort(key=lambda e: e.name.lower())
    return entries
