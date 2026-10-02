"""Small supporting modules: ffmpeg lookup, file logging, filesystem helpers, UI bridge,
edit transforms, and the OpenCV-based video service (no windows involved)."""

from __future__ import annotations

import logging
import os
import threading

import pytest
from conftest import ROOT  # noqa: F401
from PIL import Image

from services import applog, ffmpeg_locator, video_service
from services.edit_transforms import crop_box_pixels, edits_active, ffmpeg_vf_chain
from services.fsutil import same_file, unique_path
from services.ui_bridge import MainThreadDispatcher
from services.video_service import VideoState, open_video


class TestLocator:
    def test_finds_the_bundled_binary(self):
        exe = ffmpeg_locator.find_ffmpeg()
        assert os.path.isfile(exe)
        assert "imageio_ffmpeg" in exe or "ffmpeg" in os.path.basename(exe).lower()

    def test_falls_back_to_system_ffmpeg(self, monkeypatch):
        ffmpeg_locator.find_ffmpeg.cache_clear()
        import imageio_ffmpeg

        def boom():
            raise RuntimeError("no bundled binary")

        monkeypatch.setattr(imageio_ffmpeg, "get_ffmpeg_exe", boom)
        monkeypatch.setattr(ffmpeg_locator.shutil, "which", lambda name: "C:/sys/ffmpeg.exe")
        try:
            assert ffmpeg_locator.find_ffmpeg() == "C:/sys/ffmpeg.exe"
        finally:
            ffmpeg_locator.find_ffmpeg.cache_clear()

    def test_raises_a_clear_error_when_nothing_is_found(self, monkeypatch):
        ffmpeg_locator.find_ffmpeg.cache_clear()
        import imageio_ffmpeg

        monkeypatch.setattr(imageio_ffmpeg, "get_ffmpeg_exe", lambda: "Z:/missing/ffmpeg.exe")
        monkeypatch.setattr(ffmpeg_locator.shutil, "which", lambda name: None)
        try:
            with pytest.raises(ffmpeg_locator.FFmpegNotFoundError, match="ffmpeg was not found"):
                ffmpeg_locator.find_ffmpeg()
        finally:
            ffmpeg_locator.find_ffmpeg.cache_clear()

    def test_ffplay_is_optional(self, monkeypatch):
        ffmpeg_locator.find_ffplay.cache_clear()
        monkeypatch.setattr(ffmpeg_locator.shutil, "which", lambda name: None)
        monkeypatch.setattr(ffmpeg_locator, "find_ffmpeg", lambda: "Z:/nowhere/ffmpeg.exe")
        try:
            assert ffmpeg_locator.find_ffplay() is None
        finally:
            ffmpeg_locator.find_ffplay.cache_clear()


class TestAppLog:
    def test_log_path_uses_localappdata(self, monkeypatch, tmp_path):
        monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
        path = applog.log_file_path()
        assert path == tmp_path / "VideoTrimmer" / "logs" / "app.log"

    def test_setup_writes_a_file(self, monkeypatch, tmp_path):
        monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
        monkeypatch.setattr(applog, "_configured", False)
        root = logging.getLogger()
        before = list(root.handlers)
        old_level = root.level
        try:
            path = applog.setup_logging()
            logging.getLogger("t").info("hello log file")
            for h in root.handlers:
                h.flush()
            assert path is not None and path.is_file()
            assert "hello log file" in path.read_text(encoding="utf-8")
        finally:
            for h in list(root.handlers):
                if h not in before:
                    root.removeHandler(h)
                    h.close()
            root.setLevel(old_level)

    def test_unwritable_location_degrades_to_none(self, monkeypatch, tmp_path):
        blocker = tmp_path / "blocked"
        blocker.write_text("x")
        monkeypatch.setenv("LOCALAPPDATA", str(blocker))
        monkeypatch.setattr(applog, "_configured", False)
        root = logging.getLogger()
        before = list(root.handlers)
        try:
            assert applog.setup_logging() is None
        finally:
            for h in list(root.handlers):
                if h not in before:
                    root.removeHandler(h)


class TestFsUtil:
    def test_unique_path_free_name_is_unchanged(self, tmp_path):
        p = str(tmp_path / "a.mp4")
        assert unique_path(p) == p

    def test_unique_path_counts_up(self, tmp_path):
        (tmp_path / "a.mp4").write_bytes(b"1")
        (tmp_path / "a (2).mp4").write_bytes(b"1")
        assert unique_path(str(tmp_path / "a.mp4")) == str(tmp_path / "a (3).mp4")

    def test_same_file_through_dotdot(self, tmp_path):
        (tmp_path / "sub").mkdir()
        f = tmp_path / "f.mp4"
        f.write_bytes(b"1")
        assert same_file(str(f), str(tmp_path / "sub" / ".." / "f.mp4"))

    def test_different_files(self, tmp_path):
        (tmp_path / "a").write_bytes(b"1")
        (tmp_path / "b").write_bytes(b"1")
        assert not same_file(str(tmp_path / "a"), str(tmp_path / "b"))

    def test_nonexistent_paths_compare_by_name(self, tmp_path):
        assert same_file(str(tmp_path / "x.mp4"), str(tmp_path / "." / "x.mp4"))


class TestMainThreadDispatcher:
    def test_callbacks_from_workers_run_when_drained(self):
        d = MainThreadDispatcher(lambda ms, fn: None)
        out: list[int] = []
        threads = [threading.Thread(target=d.post, args=(out.append, i)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert out == []  # nothing ran on the worker threads
        assert d.drain() == 20
        assert sorted(out) == list(range(20))

    def test_a_failing_callback_does_not_block_the_rest(self):
        d = MainThreadDispatcher(lambda ms, fn: None)
        out: list[str] = []

        def bad():
            raise ValueError("ui bug")

        d.post(bad)
        d.post(out.append, "after")
        assert d.drain() == 2
        assert out == ["after"]

    def test_polling_reschedules_until_closed(self):
        scheduled: list = []
        d = MainThreadDispatcher(lambda ms, fn: scheduled.append(fn))
        d.start()
        assert len(scheduled) == 1
        scheduled.pop()()  # timer fires
        assert len(scheduled) == 1
        d.close()
        scheduled.pop()()
        assert scheduled == []
        d.post(print, "ignored after close")
        assert d.drain() == 0

    def test_stops_when_window_is_gone(self):
        scheduled: list = []
        d = MainThreadDispatcher(lambda ms, fn: scheduled.append(fn), alive=lambda: False)
        d.start()
        assert scheduled == []


class TestEditTransforms:
    def _state(self, **kw) -> VideoState:
        s = VideoState(width=200, height=100)
        for k, v in kw.items():
            setattr(s, k, v)
        return s

    def test_no_edits(self):
        s = self._state()
        assert ffmpeg_vf_chain(s) is None
        assert not edits_active(s)

    def test_crop_percentages_become_pixels(self):
        s = self._state(crop_enabled=True, crop_left_pct=10, crop_right_pct=10,
                        crop_top_pct=20, crop_bottom_pct=0)
        assert crop_box_pixels(s) == (20, 20, 160, 80)
        assert ffmpeg_vf_chain(s) == "crop=160:80:20:20"

    def test_crop_is_clamped_to_half_per_edge(self):
        s = self._state(crop_enabled=True, crop_left_pct=90, crop_right_pct=90)
        x, _, w, _ = crop_box_pixels(s)
        assert x == 100 and w >= 2

    def test_rotation_and_flips(self):
        s = self._state(rotation_cw=90, flip_horizontal=True, flip_vertical=True)
        assert ffmpeg_vf_chain(s) == "transpose=1,hflip,vflip"
        assert ffmpeg_vf_chain(self._state(rotation_cw=270)) == "transpose=2"

    def test_preview_transform_rotates_the_image(self):
        from services.edit_transforms import apply_pil_transforms

        s = self._state(rotation_cw=90)
        out = apply_pil_transforms(Image.new("RGB", (200, 100)), s)
        assert out.size == (100, 200)


class TestVideoService:
    pytestmark = pytest.mark.ffmpeg

    def test_open_video_reads_the_clip(self, clip):
        state = open_video(str(clip))
        try:
            assert state.loaded
            assert (state.width, state.height) == (160, 120)
            assert state.duration == pytest.approx(2.0, abs=0.1)
            assert state.trim_end == state.duration
            assert video_service.read_frame_at(state, 5) is not None
        finally:
            state.release()
        assert not state.loaded

    def test_open_video_with_unicode_path(self, odd_name_clip):
        state = open_video(str(odd_name_clip))
        try:
            assert state.loaded
        finally:
            state.release()

    def test_open_video_missing_file(self, tmp_path):
        with pytest.raises(RuntimeError, match="Cannot open"):
            open_video(str(tmp_path / "nope.mp4"))

    def test_thumbnails_come_back_on_the_worker_thread(self, clip):
        state = open_video(str(clip))
        done = threading.Event()
        got: list = []
        try:
            video_service.generate_thumbnails(
                state, count=6, height=30,
                on_done=lambda thumbs: (got.extend(thumbs), done.set()),
            )
            assert done.wait(30)
            assert len(got) == 6
            assert all(t.height == 30 for t in got)
        finally:
            state.release()

    def test_thumbnails_of_an_unloaded_state_return_empty_list(self):
        done = threading.Event()
        got: list = [object()]

        def cb(thumbs):
            got[:] = thumbs
            done.set()

        video_service.generate_thumbnails(VideoState(), on_done=cb)
        assert done.wait(10)
        assert got == []

    def test_time_to_frame_is_clamped(self, clip):
        state = open_video(str(clip))
        try:
            assert state.time_to_frame(-5) == 0
            assert state.time_to_frame(999) == state.frame_count - 1
        finally:
            state.release()
