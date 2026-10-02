"""Real-ffmpeg tests on a ~2 second generated clip. No window, no network."""

from __future__ import annotations

import shutil
import threading

import pytest
from conftest import file_exists, run_and_wait

from services.ffmpeg_service import TrimJob, get_metadata, run_trim

pytestmark = pytest.mark.ffmpeg


def _job(src, dst, **kw) -> TrimJob:
    defaults = {"start": 0.5, "end": 1.5}
    defaults.update(kw)
    return TrimJob(input_path=str(src), output_path=str(dst), **defaults)


class TestMetadata:
    def test_reads_generated_clip(self, clip):
        meta = get_metadata(str(clip))
        assert meta.duration == pytest.approx(2.0, abs=0.1)
        assert (meta.width, meta.height) == (160, 120)
        assert meta.fps == pytest.approx(25)
        assert meta.codec == "h264"
        assert meta.audio_codec == "aac"
        assert meta.file_size == clip.stat().st_size

    def test_clip_without_audio(self, silent_clip):
        meta = get_metadata(str(silent_clip))
        assert not meta.has_audio
        assert meta.codec == "h264"

    def test_vfr_clip_reports_a_sane_duration(self, vfr_clip):
        meta = get_metadata(str(vfr_clip))
        assert 2.0 < meta.duration < 3.5
        assert meta.fps > 0

    def test_unicode_and_spaces_in_path(self, odd_name_clip):
        assert get_metadata(str(odd_name_clip)).duration == pytest.approx(2.0, abs=0.1)

    def test_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            get_metadata(str(tmp_path / "nope.mp4"))

    def test_garbage_file_raises_readable_error(self, tmp_path):
        bad = tmp_path / "bad.mp4"
        bad.write_bytes(b"this is not a video" * 50)
        with pytest.raises(RuntimeError, match="ffmpeg said"):
            get_metadata(str(bad))


class TestTrim:
    def test_stream_copy_fast_path(self, clip, tmp_path):
        out = tmp_path / "copy.mp4"
        job = _job(clip, out)
        seen = run_and_wait(job)
        assert job.error == ""
        assert job.done
        assert file_exists(out)
        # Copy cuts snap to a keyframe (every 10 frames = 0.4 s here), so be generous.
        assert 0.5 <= get_metadata(str(out)).duration <= 1.6
        assert job.progress == 100.0
        assert all(0 <= p <= 100 for p in seen)

    def test_reencode_is_frame_accurate(self, clip, tmp_path):
        out = tmp_path / "enc.mp4"
        job = _job(clip, out, copy_streams=False, crf=28, start=0.4, end=1.4)
        run_and_wait(job)
        assert job.error == ""
        assert get_metadata(str(out)).duration == pytest.approx(1.0, abs=0.15)

    def test_progress_reaches_the_end(self, clip, tmp_path):
        out = tmp_path / "p.mp4"
        job = _job(clip, out, copy_streams=False, crf=30, start=0.0, end=2.0)
        seen = run_and_wait(job)
        assert job.progress == 100.0
        assert seen == sorted(seen)

    def test_strip_audio(self, clip, tmp_path):
        out = tmp_path / "mute.mp4"
        job = _job(clip, out, include_audio=False)
        run_and_wait(job)
        assert job.error == ""
        assert not get_metadata(str(out)).has_audio

    def test_clip_with_no_audio_stream(self, silent_clip, tmp_path):
        out = tmp_path / "silent_out.mp4"
        job = _job(silent_clip, out, copy_streams=False, crf=28)
        run_and_wait(job)
        assert job.error == ""
        assert not get_metadata(str(out)).has_audio

    def test_vfr_phone_style_footage(self, vfr_clip, tmp_path):
        out = tmp_path / "vfr_out.mp4"
        job = _job(vfr_clip, out, copy_streams=False, crf=28, start=0.5, end=2.0)
        run_and_wait(job)
        assert job.error == ""
        assert 1.0 < get_metadata(str(out)).duration < 2.0

    def test_unicode_and_spaces_in_input_and_output(self, odd_name_clip, tmp_path):
        out_dir = tmp_path / "out folder ü"
        out_dir.mkdir()
        out = out_dir / "résultat 中.mp4"
        job = _job(odd_name_clip, out)
        run_and_wait(job)
        assert job.error == ""
        assert file_exists(out)

    def test_end_beyond_duration_is_clamped_not_an_error(self, clip, tmp_path):
        out = tmp_path / "long.mp4"
        job = _job(clip, out, start=1.0, end=60.0, source_duration=2.0,
                   copy_streams=False, crf=28)
        run_and_wait(job)
        assert job.error == ""
        assert job.end == 2.0
        assert get_metadata(str(out)).duration == pytest.approx(1.0, abs=0.2)

    def test_very_short_clip(self, clip, tmp_path):
        out = tmp_path / "short.mp4"
        job = _job(clip, out, start=1.0, end=1.2, copy_streams=False, crf=28)
        run_and_wait(job)
        assert job.error == ""
        assert file_exists(out)

    def test_in_equals_out_is_rejected_without_running_ffmpeg(self, clip, tmp_path):
        out = tmp_path / "x.mp4"
        job = _job(clip, out, start=1.0, end=1.0)
        run_and_wait(job)
        assert "same" in job.error
        assert not out.exists()

    def test_start_past_end_of_video_is_rejected(self, clip, tmp_path):
        job = _job(clip, tmp_path / "x.mp4", start=5.0, end=6.0, source_duration=2.0)
        run_and_wait(job)
        assert "past the end" in job.error

    def test_never_overwrites_the_source(self, clip, tmp_path):
        victim = tmp_path / "victim.mp4"
        shutil.copy(clip, victim)
        before = victim.read_bytes()
        job = _job(victim, victim)
        run_and_wait(job)
        assert "overwrite the source" in job.error
        assert victim.read_bytes() == before

    def test_source_overwrite_detected_through_a_dotdot_spelling(self, clip, tmp_path):
        victim = tmp_path / "victim.mp4"
        shutil.copy(clip, victim)
        before = victim.read_bytes()
        (tmp_path / "sub").mkdir()
        job = _job(victim, tmp_path / "sub" / ".." / "victim.mp4")
        run_and_wait(job)
        assert "overwrite the source" in job.error
        assert victim.read_bytes() == before

    def test_missing_output_folder(self, clip, tmp_path):
        job = _job(clip, tmp_path / "no" / "such" / "dir" / "o.mp4")
        run_and_wait(job)
        assert "folder does not exist" in job.error

    def test_missing_source(self, tmp_path):
        job = _job(tmp_path / "gone.mp4", tmp_path / "o.mp4")
        run_and_wait(job)
        assert "not found" in job.error


class TestFailureIsSurfaced:
    def test_corrupt_input_reports_ffmpeg_error_and_leaves_no_partial_file(self, tmp_path):
        bad = tmp_path / "corrupt.mp4"
        bad.write_bytes(b"\x00\x01garbage" * 200)
        out = tmp_path / "o.mp4"
        job = _job(bad, out, start=0.0, end=1.0)
        run_and_wait(job)
        assert job.error.startswith("ffmpeg failed")
        assert "damaged" in job.error
        assert not out.exists()

    def test_copy_into_webm_gives_a_helpful_message(self, clip, tmp_path):
        out = tmp_path / "o.webm"
        job = _job(clip, out, include_audio=False)  # h264 stream copy into webm is illegal
        run_and_wait(job)
        assert job.error
        assert "re-encode" in job.error
        assert not out.exists()

    def test_webm_reencode_works(self, clip, tmp_path):
        out = tmp_path / "o.webm"
        job = _job(clip, out, copy_streams=False, crf=40, start=0.0, end=1.0)
        run_and_wait(job)
        assert job.error == ""
        assert get_metadata(str(out)).codec == "vp9"

    def test_on_done_always_fires_even_if_callbacks_raise(self, clip, tmp_path):
        finished = threading.Event()

        def bad_progress(_p):
            raise RuntimeError("boom")

        job = _job(clip, tmp_path / "o.mp4", copy_streams=False, crf=30, start=0, end=1.5)
        run_trim(job, on_progress=bad_progress, on_done=lambda _j: finished.set())
        assert finished.wait(60)
        assert job.error == ""


class TestCancel:
    def test_cancel_before_start_is_honoured(self, clip, tmp_path):
        out = tmp_path / "c.mp4"
        job = _job(clip, out, copy_streams=False, crf=18, start=0.0, end=2.0)
        job.cancel_event.set()
        run_and_wait(job)
        assert job.error == "Cancelled"
        assert not out.exists()
