# From: services/ffmpeg_service.py:129
# Build the ffmpeg command list for a trim job.

def build_trim_cmd(job: TrimJob) -> list[str]:
    """Build the ffmpeg command list for a trim job."""
    cmd = [FFMPEG_BIN, "-y"]

    # Input seeking (fast) then precise trim
    cmd += ["-ss", str(job.start)]
    cmd += ["-i", job.input_path]
    cmd += ["-to", str(job.end - job.start)]

    video_must_encode = bool(job.video_filter)

    if video_must_encode:
        if job.video_filter:
            cmd += ["-vf", job.video_filter]
        cmd += ["-c:v", "libx264", "-preset", "medium"]
        crf = job.crf if job.crf is not None else 23
        cmd += ["-crf", str(crf)]
        if job.include_audio:
            if job.copy_streams:
                cmd += ["-c:a", "copy"]
            else:
                cmd += ["-c:a", "aac", "-b:a", "192k"]
    elif job.copy_streams:
        cmd += ["-c", "copy"]
    else:
        cmd += ["-c:v", "libx264", "-preset", "medium"]
        if job.crf is not None:
            cmd += ["-crf", str(job.crf)]
        if job.include_audio:
            cmd += ["-c:a", "aac", "-b:a", "192k"]

    if not job.include_audio:
        cmd += ["-an"]

    cmd += ["-avoid_negative_ts", "make_zero"]
    cmd += [job.output_path]
    return cmd
