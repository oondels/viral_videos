"""Unit tests for T-017: FFmpeg adapter and video utilities."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.adapters.ffmpeg_adapter import (
    FFmpegError,
    concat_audio,
    run_ffmpeg,
    scale_and_trim_video,
)
from app.utils.audio_utils import write_silence_wav
from app.utils.ffprobe_utils import get_media_duration, get_video_dimensions
from app.utils.video_utils import make_color_video


# ---------------------------------------------------------------------------
# run_ffmpeg
# ---------------------------------------------------------------------------

class TestRunFfmpeg:
    def test_valid_command_succeeds(self, tmp_path):
        out = tmp_path / "out.wav"
        write_silence_wav(out, duration_sec=1.0)
        # ffmpeg -version should always succeed
        run_ffmpeg(["ffmpeg", "-version"])

    def test_invalid_command_raises_ffmpeg_error(self, tmp_path):
        with pytest.raises(FFmpegError):
            run_ffmpeg(["ffmpeg", "-i", str(tmp_path / "nonexistent.wav"), "-f", "null", "-"])


# ---------------------------------------------------------------------------
# concat_audio
# ---------------------------------------------------------------------------

class TestConcatAudio:
    def test_concatenates_two_wav_files(self, tmp_path):
        a = tmp_path / "a.wav"
        b = tmp_path / "b.wav"
        out = tmp_path / "out.wav"
        write_silence_wav(a, duration_sec=1.0)
        write_silence_wav(b, duration_sec=1.0)
        concat_audio([a, b], out)
        assert out.exists()
        dur = get_media_duration(out)
        assert abs(dur - 2.0) < 0.1

    def test_output_duration_matches_sum_of_inputs(self, tmp_path):
        files = []
        for i, d in enumerate([0.5, 1.0, 1.5]):
            p = tmp_path / f"seg_{i}.wav"
            write_silence_wav(p, duration_sec=d)
            files.append(p)
        out = tmp_path / "master.wav"
        concat_audio(files, out)
        dur = get_media_duration(out)
        assert abs(dur - 3.0) < 0.1

    def test_empty_input_raises_value_error(self, tmp_path):
        with pytest.raises(ValueError, match="at least one"):
            concat_audio([], tmp_path / "out.wav")

    def test_concat_list_written_alongside_output(self, tmp_path):
        a = tmp_path / "a.wav"
        write_silence_wav(a, duration_sec=1.0)
        out = tmp_path / "out.wav"
        concat_audio([a], out)
        assert (tmp_path / "concat_list.txt").exists()


# ---------------------------------------------------------------------------
# scale_and_trim_video
# ---------------------------------------------------------------------------

class TestScaleAndTrimVideo:
    def test_output_file_created(self, tmp_path):
        src = tmp_path / "src.mp4"
        make_color_video(src, duration_sec=5.0, width=640, height=480)
        out = tmp_path / "out.mp4"
        scale_and_trim_video(src, out, width=1080, height=1920, duration_sec=3.0)
        assert out.exists()

    def test_output_dimensions_are_target(self, tmp_path):
        src = tmp_path / "src.mp4"
        make_color_video(src, duration_sec=5.0, width=640, height=480)
        out = tmp_path / "out.mp4"
        scale_and_trim_video(src, out, width=1080, height=1920, duration_sec=3.0)
        w, h = get_video_dimensions(out)
        assert w == 1080
        assert h == 1920

    def test_output_duration_matches_requested(self, tmp_path):
        src = tmp_path / "src.mp4"
        make_color_video(src, duration_sec=10.0, width=640, height=480)
        out = tmp_path / "out.mp4"
        scale_and_trim_video(src, out, width=1080, height=1920, duration_sec=3.0)
        dur = get_media_duration(out)
        assert abs(dur - 3.0) < 0.1

    def test_loop_extends_short_source(self, tmp_path):
        src = tmp_path / "src.mp4"
        make_color_video(src, duration_sec=2.0, width=640, height=480)
        out = tmp_path / "out.mp4"
        scale_and_trim_video(src, out, width=1080, height=1920, duration_sec=5.0, loop=True)
        dur = get_media_duration(out)
        assert dur >= 5.0 - (1.0 / 30.0)


# ---------------------------------------------------------------------------
# ffprobe_utils extensions
# ---------------------------------------------------------------------------

class TestGetMediaDuration:
    def test_audio_duration(self, tmp_path):
        p = tmp_path / "a.wav"
        write_silence_wav(p, duration_sec=2.0)
        assert abs(get_media_duration(p) - 2.0) < 0.05

    def test_video_duration(self, tmp_path):
        p = tmp_path / "v.mp4"
        make_color_video(p, duration_sec=3.0)
        assert abs(get_media_duration(p) - 3.0) < 0.1

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(RuntimeError):
            get_media_duration(tmp_path / "ghost.wav")


class TestGetVideoDimensions:
    def test_returns_correct_dimensions(self, tmp_path):
        p = tmp_path / "v.mp4"
        make_color_video(p, duration_sec=1.0, width=320, height=240)
        w, h = get_video_dimensions(p)
        assert w == 320
        assert h == 240

    def test_audio_only_file_raises(self, tmp_path):
        p = tmp_path / "a.wav"
        write_silence_wav(p, duration_sec=1.0)
        with pytest.raises(RuntimeError, match="No video stream"):
            get_video_dimensions(p)
