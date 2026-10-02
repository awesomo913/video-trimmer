"""Batch split: segment maths, naming, folder scan, and partial-failure behaviour."""

from __future__ import annotations

import threading

import pytest
from conftest import run_and_wait  # noqa: F401  (keeps conftest import order explicit)

from services import batch_split_service as bs
from services.batch_split_service import (
    BatchFileEntry,
    BatchSplitJob,
    ScanError,
    SplitConfig,
    build_output_path,
    compute_segments,
    default_output_folder,
    run_batch,
    scan_folder,
)
from services.ffmpeg_service import get_metadata


class TestComputeSegments:
    def test_equal_parts(self):
        segs = compute_segments(12.0, SplitConfig(mode="equal", n_parts=4))
        assert segs == [(0.0, 3.0), (3.0, 6.0), (6.0, 9.0), (9.0, 12.0)]

    def test_equal_parts_cover_the_whole_file_without_gaps(self):
        segs = compute_segments(10.0, SplitConfig(mode="equal", n_parts=3))
        assert segs[0][0] == 0.0 and segs[-1][1] == 10.0
        for (_, end), (start, _) in zip(segs, segs[1:], strict=False):
            assert end == pytest.approx(start)

    def test_duration_chunks_with_remainder(self):
        segs = compute_segments(50.0, SplitConfig(mode="duration", chunk_seconds=20))
        assert segs == [(0.0, 20.0), (20.0, 40.0), (40.0, 50.0)]

    def test_duration_mode_skips_files_shorter_than_chunk(self):
        assert compute_segments(12.0, SplitConfig(mode="duration", chunk_seconds=20)) == []

    def test_tiny_leftover_is_folded_into_previous_part(self):
        segs = compute_segments(60.02, SplitConfig(mode="duration", chunk_seconds=20))
        assert len(segs) == 3
        assert segs[-1][1] == pytest.approx(60.02)

    def test_equal_split_of_a_very_short_file_is_skipped(self):
        assert compute_segments(0.2, SplitConfig(mode="equal", n_parts=8)) == []

    def test_zero_or_negative_duration(self):
        assert compute_segments(0, SplitConfig()) == []
        assert compute_segments(-5, SplitConfig()) == []

    def test_unknown_mode(self):
        assert compute_segments(10, SplitConfig(mode="weird")) == []


class TestNaming:
    def test_part_names(self):
        entry = BatchFileEntry(path="C:/v/holiday.mp4")
        assert build_output_path(entry, 0, 4, "out", ".mp4").endswith("holiday_part_1_of_4.mp4")

    def test_zero_padding_when_ten_or_more(self):
        entry = BatchFileEntry(path="a.mkv")
        assert build_output_path(entry, 2, 12, "o", ".mkv").endswith("a_part_03_of_12.mkv")

    def test_default_output_folder_is_a_subfolder(self, tmp_path):
        assert default_output_folder(str(tmp_path)).startswith(str(tmp_path))


class TestScan:
    def test_only_videos_are_listed_sorted_case_insensitively(self, tmp_path, monkeypatch):
        for name in ("b.mp4", "A.MKV", "notes.txt", "c.jpg"):
            (tmp_path / name).write_bytes(b"x")
        (tmp_path / "sub").mkdir()
        monkeypatch.setattr(bs, "get_metadata", lambda p: type("M", (), {"duration": 9.0})())
        names = [e.name for e in scan_folder(str(tmp_path))]
        assert names == ["A.MKV", "b.mp4"]

    def test_unreadable_file_does_not_abort_the_scan(self, tmp_path, monkeypatch):
        (tmp_path / "good.mp4").write_bytes(b"x")
        (tmp_path / "bad.mp4").write_bytes(b"x")

        def fake(path):
            if path.endswith("bad.mp4"):
                raise RuntimeError("moov atom not found")
            return type("M", (), {"duration": 5.0})()

        monkeypatch.setattr(bs, "get_metadata", fake)
        entries = {e.name: e for e in scan_folder(str(tmp_path))}
        assert entries["good.mp4"].status == bs.STATUS_PENDING
        assert entries["bad.mp4"].status == bs.STATUS_UNREADABLE
        assert "moov" in entries["bad.mp4"].meta_error

    def test_zero_duration_is_unreadable(self, tmp_path, monkeypatch):
        (tmp_path / "z.mp4").write_bytes(b"x")
        monkeypatch.setattr(bs, "get_metadata", lambda p: type("M", (), {"duration": 0.0})())
        assert scan_folder(str(tmp_path))[0].status == bs.STATUS_UNREADABLE

    def test_missing_folder(self, tmp_path):
        with pytest.raises(ScanError):
            scan_folder(str(tmp_path / "nope"))

    def test_empty_folder(self, tmp_path):
        assert scan_folder(str(tmp_path)) == []


def _run(job: BatchSplitJob):
    done = threading.Event()
    result: dict = {}
    events: list[tuple[str, str]] = []

    def finished(_job, err):
        result["error"] = err
        done.set()

    run_batch(
        job,
        on_file_start=lambda e: events.append(("start", e.name)),
        on_file_done=lambda e: events.append(("done", e.name)),
        on_batch_done=finished,
    )
    assert done.wait(120)
    return result["error"], events


@pytest.mark.ffmpeg
class TestRunBatchReal:
    def test_splits_a_real_clip_into_parts(self, clip, tmp_path):
        src = tmp_path / "in"
        src.mkdir()
        (src / "movie.mp4").write_bytes(clip.read_bytes())
        entries = scan_folder(str(src))
        cfg = SplitConfig(mode="equal", n_parts=2, quality_key="Medium (CRF 23)")
        job = BatchSplitJob(str(src), default_output_folder(str(src)), entries, cfg)
        error, _ = _run(job)
        assert error == ""
        assert entries[0].status == bs.STATUS_DONE
        parts = sorted((src / "split_output").glob("movie_part_*_of_2.mp4"))
        assert len(parts) == 2
        for part in parts:
            assert get_metadata(str(part)).duration == pytest.approx(1.0, abs=0.2)

    def test_rerun_never_overwrites_earlier_results(self, clip, tmp_path):
        src = tmp_path / "in"
        src.mkdir()
        (src / "m.mp4").write_bytes(clip.read_bytes())
        out = default_output_folder(str(src))
        for _ in range(2):
            entries = scan_folder(str(src))
            cfg = SplitConfig(mode="equal", n_parts=2, quality_key="High (CRF 18)")
            _run(BatchSplitJob(str(src), out, entries, cfg))
        names = sorted(p.name for p in (src / "split_output").iterdir())
        assert len(names) == 4
        assert "m_part_1_of_2 (2).mp4" in names


class TestRunBatchFailures:
    def test_one_bad_file_is_reported_and_the_rest_continue(self, tmp_path, monkeypatch):
        calls: list[str] = []

        def fake_run_trim(job, on_progress=None, on_done=None):
            calls.append(job.input_path)
            if job.input_path.endswith("bad.mp4"):
                job.error = "ffmpeg failed: Invalid data"
            job.done = True
            if on_done:
                on_done(job)

        monkeypatch.setattr(bs, "run_trim", fake_run_trim)
        files = [
            BatchFileEntry(path=str(tmp_path / "a.mp4"), duration=10.0),
            BatchFileEntry(path=str(tmp_path / "bad.mp4"), duration=10.0),
            BatchFileEntry(path=str(tmp_path / "c.mp4"), duration=10.0),
        ]
        job = BatchSplitJob(str(tmp_path), str(tmp_path / "out"), files,
                            SplitConfig(mode="equal", n_parts=2))
        error, events = _run(job)
        assert error == ""
        assert [f.status for f in files] == [bs.STATUS_DONE, bs.STATUS_FAILED, bs.STATUS_DONE]
        assert files[0].error == ""
        assert "Invalid data" in files[1].error
        assert "part 1 of 2" in files[1].error
        # the bad file stopped after its first part; the others ran both parts
        assert sum(c.endswith("bad.mp4") for c in calls) == 1
        assert sum(c.endswith("c.mp4") for c in calls) == 2
        assert ("done", "c.mp4") in events

    def test_unreadable_entries_are_skipped_and_short_files_marked_skipped(self, tmp_path,
                                                                           monkeypatch):
        monkeypatch.setattr(bs, "run_trim", lambda job, on_progress=None, on_done=None: (
            setattr(job, "done", True), on_done and on_done(job)))
        files = [
            BatchFileEntry(path="x.mp4", duration=0.0, status=bs.STATUS_UNREADABLE),
            BatchFileEntry(path="short.mp4", duration=5.0),
        ]
        job = BatchSplitJob(str(tmp_path), str(tmp_path / "o"), files,
                            SplitConfig(mode="duration", chunk_seconds=30))
        error, _ = _run(job)
        assert error == ""
        assert files[0].status == bs.STATUS_UNREADABLE
        assert files[1].status == bs.STATUS_SKIPPED

    def test_cancel_stops_the_batch(self, tmp_path, monkeypatch):
        job_holder: dict = {}

        def fake_run_trim(job, on_progress=None, on_done=None):
            job_holder["job"].cancel_event.set()  # user presses Cancel during the first part
            job.error = "Cancelled"
            job.done = True
            if on_done:
                on_done(job)

        monkeypatch.setattr(bs, "run_trim", fake_run_trim)
        files = [BatchFileEntry(path="a.mp4", duration=10.0),
                 BatchFileEntry(path="b.mp4", duration=10.0)]
        job = BatchSplitJob(str(tmp_path), str(tmp_path / "o"), files, SplitConfig(n_parts=2))
        job_holder["job"] = job
        error, _ = _run(job)
        assert error == "cancelled"
        assert files[1].status == bs.STATUS_PENDING

    def test_crash_inside_the_runner_still_reports_back(self, tmp_path, monkeypatch):
        def explode(*_a, **_k):
            raise ValueError("kaboom")

        monkeypatch.setattr(bs, "compute_segments", explode)
        job = BatchSplitJob(str(tmp_path), str(tmp_path / "o"),
                            [BatchFileEntry(path="a.mp4", duration=10.0)], SplitConfig())
        error, _ = _run(job)
        assert "kaboom" in error

    def test_unwritable_output_folder_is_reported(self, tmp_path):
        blocker = tmp_path / "file.txt"
        blocker.write_text("x")
        job = BatchSplitJob(str(tmp_path), str(blocker / "sub"), [], SplitConfig())
        error, _ = _run(job)
        assert "output folder" in error.lower()
