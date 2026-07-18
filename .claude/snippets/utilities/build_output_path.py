# From: services/batch_split_service.py:164
# `<basename>_part_<n>_of_<N>.<ext>`, zero-padded to width if N >= 10.

def build_output_path(
    entry: BatchFileEntry, seg_idx: int, total: int,
    output_folder: str, ext: str,
) -> str:
    """`<basename>_part_<n>_of_<N>.<ext>`, zero-padded to width if N >= 10."""
    width = 2 if total >= 10 else 1
    name = f"{entry.basename}_part_{seg_idx + 1:0{width}d}_of_{total}{ext}"
    return os.path.join(output_folder, name)
