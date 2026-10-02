"""Pure-logic tests: time helpers, metadata parsing, trim validation, command building."""

from __future__ import annotations

import pytest

from services import ffmpeg_service as fs
from services.ffmpeg_service import (
    TrimError,
    TrimJob,
    build_trim_cmd,
    format_time,
    parse_ffmpeg_info,
    parse_time,
    summarize_ffmpeg_error,
    validate_trim,
)

MP4_INFO = """\
Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'C:/v/a.mp4':
  Metadata:
    major_brand     : isom
  Duration: 00:01:02.50, start: 0.000000, bitrate: 2145 kb/s
  Stream #0:0[0x1](und): Video: h264 (High) (avc1 / 0x31637661), yuv420p(progressive), 1920x1080 [SAR 1:1 DAR 16:9], 2000 kb/s, 29.97 fps, 29.97 tbr, 30k tbn (default)
      Metadata:
        handler_name    : VideoHandler
  Stream #0:1[0x2](und): Audio: aac (LC) (mp4a / 0x6134706D), 48000 Hz, stereo, fltp, 128 kb/s (default)
At least one output file must be specified
"""  # noqa: E501

ROTATED_INFO = """\
Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'phone.mov':
  Duration: 00:00:10.00, start: 0.000000, bitrate: 17000 kb/s
  Stream #0:0[0x1](und): Video: hevc (Main) (hvc1 / 0x31637668), yuv420p10le(tv), 1920x1080, 16900 kb/s, 59.94 fps, 59.94 tbr, 600 tbn (default)
      Side data:
        displaymatrix: rotation of -90.00 degrees
"""  # noqa: E501

MKV_NO_AUDIO = """\
Input #0, matroska,webm, from 'x.mkv':
  Duration: 00:00:05.00, start: 0.000000, bitrate: 900 kb/s
  Stream #0:0(eng): Video: vp9 (Profile 0), yuv420p(tv), 640x360, SAR 1:1 DAR 16:9, 25 fps, 25 tbr, 1k tbn (default)
"""  # noqa: E501

COVER_ART = """\
Input #0, mp3, from 'song.mp3':
  Duration: 00:03:00.00, start: 0.025057, bitrate: 192 kb/s
  Stream #0:0: Audio: mp3, 44100 Hz, stereo, fltp, 192 kb/s
  Stream #0:1: Video: mjpeg (Baseline), yuvj420p(pc), 500x500, 90k tbr, 90k tbn (attached pic)
"""


MOOV_ERROR = "moov atom not found\nInvalid data found when processing input"


class TestTimeHelpers:
    @pytest.mark.parametrize("seconds, expected", [
        (0, "00:00.00"), (5.5, "00:05.50"), (65, "01:05.00"),
        (3725.25, "1:02:05.25"), (-3, "00:00.00"), (float("nan"), "00:00.00"),
    ])
    def test_format_time(self, seconds, expected):
        assert format_time(seconds) == expected

    @pytest.mark.parametrize("text, expected", [
        ("12", 12.0), ("1:23.45", 83.45), ("1:02:03", 3723.0), (" 0:05 ", 5.0),
    ])
    def test_parse_time(self, text, expected):
        assert parse_time(text) == pytest.approx(expected)

    @pytest.mark.parametrize("text", ["abc", "", "1:2:3:4", "-5", "nan", "inf", "1:-2"])
    def test_parse_time_rejects_garbage(self, text):
        with pytest.raises(ValueError, match=r"."):
            parse_time(text)


class TestParseFfmpegInfo:
    def test_normal_mp4(self):
        meta = parse_ffmpeg_info(MP4_INFO, "a.mp4")
        assert meta.duration == pytest.approx(62.5)
        assert (meta.width, meta.height) == (1920, 1080)
        assert meta.fps == pytest.approx(29.97)
        assert meta.codec == "h264"
        assert meta.audio_codec == "aac"
        assert meta.has_audio
        assert meta.bitrate == 2145000
        assert "mp4" in meta.format_name

    def test_hex_codec_tag_is_not_mistaken_for_resolution(self):
        meta = parse_ffmpeg_info(MP4_INFO)
        assert meta.width == 1920

    def test_phone_rotation_swaps_dimensions(self):
        meta = parse_ffmpeg_info(ROTATED_INFO)
        assert (meta.width, meta.height) == (1080, 1920)
        assert meta.fps == pytest.approx(59.94)

    def test_no_audio_stream(self):
        meta = parse_ffmpeg_info(MKV_NO_AUDIO)
        assert not meta.has_audio
        assert meta.codec == "vp9"
        assert meta.fps == 25

    def test_attached_cover_art_is_not_the_video(self):
        meta = parse_ffmpeg_info(COVER_ART)
        assert meta.audio_codec == "mp3"
        assert meta.codec == ""

    def test_unreadable_text_raises(self):
        with pytest.raises(RuntimeError, match="No audio or video"):
            parse_ffmpeg_info("moov atom not found\nInvalid data found when processing input")

    def test_duration_na_gives_zero(self):
        text = MP4_INFO.replace("Duration: 00:01:02.50", "Duration: N/A")
        assert parse_ffmpeg_info(text).duration == 0.0


class TestValidateTrim:
    def test_ok(self):
        assert validate_trim(1.0, 3.0, 10.0) == (1.0, 3.0)

    def test_in_equals_out(self):
        with pytest.raises(TrimError, match="same"):
            validate_trim(2.0, 2.0)

    def test_reversed(self):
        with pytest.raises(TrimError, match="after"):
            validate_trim(5.0, 2.0)

    def test_end_beyond_duration_is_clamped(self):
        assert validate_trim(2.0, 99.0, 10.0) == (2.0, 10.0)

    def test_start_beyond_duration(self):
        with pytest.raises(TrimError, match="past the end"):
            validate_trim(10.0, 12.0, 10.0)

    def test_negative_start_becomes_zero(self):
        assert validate_trim(-1.0, 2.0)[0] == 0.0

    def test_shorter_than_a_frame(self):
        with pytest.raises(TrimError, match="shorter"):
            validate_trim(1.0, 1.01)

    def test_non_finite(self):
        with pytest.raises(TrimError, match="real numbers"):
            validate_trim(float("nan"), 3.0)

    def test_unknown_duration_leaves_end_alone(self):
        assert validate_trim(1.0, 500.0, None) == (1.0, 500.0)


def _job(**kw) -> TrimJob:
    defaults = {"input_path": "in.mp4", "output_path": "out.mp4", "start": 1.0, "end": 3.5}
    defaults.update(kw)
    return TrimJob(**defaults)


@pytest.fixture(autouse=True)
def _fake_ffmpeg(monkeypatch):
    monkeypatch.setattr(fs, "find_ffmpeg", lambda: "FFMPEG")


class TestBuildTrimCmd:
    def test_copy_fast_path(self):
        cmd = build_trim_cmd(_job())
        assert cmd[0] == "FFMPEG"
        assert cmd[cmd.index("-ss") + 1] == "1.000"
        assert cmd[cmd.index("-t") + 1] == "2.500"
        assert cmd[cmd.index("-i") + 1] == "in.mp4"
        assert cmd[cmd.index("-c:v") + 1] == "copy"
        assert cmd[cmd.index("-c:a") + 1] == "copy"
        assert cmd[-1] == "out.mp4"
        assert "-nostdin" in cmd

    def test_seek_is_before_input(self):
        cmd = build_trim_cmd(_job())
        assert cmd.index("-ss") < cmd.index("-i")

    def test_reencode_uses_x264_and_crf(self):
        cmd = build_trim_cmd(_job(copy_streams=False, crf=28))
        assert cmd[cmd.index("-c:v") + 1] == "libx264"
        assert cmd[cmd.index("-crf") + 1] == "28"
        assert "yuv420p" in cmd
        assert cmd[cmd.index("-c:a") + 1] == "aac"

    def test_reencode_default_crf(self):
        cmd = build_trim_cmd(_job(copy_streams=False, crf=None))
        assert cmd[cmd.index("-crf") + 1] == "23"

    def test_no_audio(self):
        cmd = build_trim_cmd(_job(include_audio=False))
        assert "-an" in cmd
        assert "-c:a" not in cmd

    def test_filter_forces_video_reencode_but_copies_audio(self):
        cmd = build_trim_cmd(_job(video_filter="hflip"))
        assert cmd[cmd.index("-vf") + 1] == "hflip"
        assert cmd[cmd.index("-c:v") + 1] == "libx264"
        assert cmd[cmd.index("-c:a") + 1] == "copy"

    def test_webm_never_gets_h264_or_aac(self):
        cmd = build_trim_cmd(_job(output_path="out.webm", copy_streams=False, crf=30))
        assert cmd[cmd.index("-c:v") + 1] == "libvpx-vp9"
        assert cmd[cmd.index("-c:a") + 1] == "libopus"

    def test_webm_with_filter_and_copy_quality_reencodes_audio_too(self):
        cmd = build_trim_cmd(_job(output_path="out.webm", video_filter="vflip"))
        assert cmd[cmd.index("-c:a") + 1] == "libopus"

    def test_mp4_gets_faststart_and_mkv_does_not(self):
        assert "+faststart" in build_trim_cmd(_job(output_path="o.mp4"))
        assert "+faststart" not in build_trim_cmd(_job(output_path="o.mkv"))

    def test_streams_selected_explicitly_so_data_tracks_are_dropped(self):
        cmd = build_trim_cmd(_job())
        assert "0:v" in cmd and "0:a?" in cmd

    def test_paths_with_spaces_and_unicode_stay_single_arguments(self):
        cmd = build_trim_cmd(_job(input_path="C:/my videos/caf\u00e9 1.mp4",
                                  output_path="C:/out dir/\u4e2d.mp4"))
        assert "C:/my videos/caf\u00e9 1.mp4" in cmd
        assert cmd[-1] == "C:/out dir/\u4e2d.mp4"


class TestSummarizeError:
    def test_known_container_problem_gets_plain_hint(self):
        text = "[webm @ 0x1] Only VP8 or VP9 video allowed\nCould not find tag for codec h264"
        assert "re-encode" in summarize_ffmpeg_error(text)

    def test_unknown_error_returns_last_lines(self):
        text = "ffmpeg version 7\nsomething odd\nUnknown encoder foo"
        out = summarize_ffmpeg_error(text)
        assert "Unknown encoder" in out
        assert "ffmpeg version" not in out

    def test_unreadable_source_gets_plain_hint(self):
        assert "damaged" in summarize_ffmpeg_error(MOOV_ERROR)

    def test_progress_lines_are_ignored(self):
        text = "frame=  10 fps=0.0 q=-1.0 size=0kB time=00:00:00.40\nreal error here"
        assert summarize_ffmpeg_error(text) == "real error here"

    def test_empty(self):
        assert "no details" in summarize_ffmpeg_error("")
