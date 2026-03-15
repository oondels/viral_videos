"""Unit tests for T-016: background selection, looping, trimming, and normalisation."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from app.core.contracts import ValidatedJob
from app.core.job_context import JobContext
from app.modules.background_selector import BackgroundError, prepare_background
from app.services.file_service import init_workspace
from app.utils.ffprobe_utils import get_audio_duration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_job(**kwargs: Any) -> ValidatedJob:
    defaults = dict(
        job_id="job_2026_03_15_016",
        topic="test topic",
        duration_target_sec=30,
        characters=["char_a", "char_b"],
        background_style="auto",
        output_preset="shorts_default",
    )
    defaults.update(kwargs)
    return ValidatedJob(**defaults)


def _make_ctx(
    tmp_path: Path,
    job_id: str = "job_2026_03_15_016",
    background_style: str = "auto",
) -> JobContext:
    import os

    os.chdir(tmp_path)
    job = _make_job(job_id=job_id, background_style=background_style)
    ctx = JobContext(job=job)
    init_workspace(ctx)
    return ctx


def _make_video(path: Path, duration_sec: float = 5.0, size: str = "640x480") -> None:
    """Create a minimal test video using FFmpeg lavfi color source."""
    path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=blue:s={size}:r=30:d={duration_sec}",
            "-c:v", "libx264",
            "-t", str(duration_sec),
            str(path),
        ],
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, f"Failed to create test video: {result.stderr.decode()}"


def _setup_category(tmp_path: Path, category: str, n: int = 1, duration_sec: float = 5.0) -> list[Path]:
    """Create n test MP4 files in a background category folder."""
    cat_dir = tmp_path / "assets" / "backgrounds" / category
    cat_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for i in range(n):
        p = cat_dir / f"bg_{i:02d}.mp4"
        _make_video(p, duration_sec=duration_sec)
        files.append(p)
    return files


# ---------------------------------------------------------------------------
# Tests: selection
# ---------------------------------------------------------------------------

class TestBackgroundSelection:
    def test_explicit_style_uses_that_category(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_category(tmp_path, "slime", n=1, duration_sec=5.0)
        ctx = _make_ctx(tmp_path, background_style="slime")
        result = prepare_background(ctx, required_duration_sec=3.0)
        assert result.exists()
        assert result == ctx.prepared_background()

    def test_auto_selection_is_deterministic(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_category(tmp_path, "misc", n=3, duration_sec=5.0)

        ctx1 = _make_ctx(tmp_path, job_id="job_2026_03_15_016", background_style="auto")
        ctx2 = _make_ctx(tmp_path, job_id="job_2026_03_15_016", background_style="auto")

        from app.modules.background_selector import _select_background
        bg1 = _select_background("auto", "job_2026_03_15_016")
        bg2 = _select_background("auto", "job_2026_03_15_016")
        assert bg1 == bg2

    def test_no_assets_for_style_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "assets" / "backgrounds" / "slime").mkdir(parents=True)
        ctx = _make_ctx(tmp_path, background_style="slime")
        with pytest.raises(BackgroundError, match="No background assets"):
            prepare_background(ctx, required_duration_sec=3.0)

    def test_no_assets_for_auto_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "assets" / "backgrounds").mkdir(parents=True)
        ctx = _make_ctx(tmp_path, background_style="auto")
        with pytest.raises(BackgroundError, match="No background assets"):
            prepare_background(ctx, required_duration_sec=3.0)


# ---------------------------------------------------------------------------
# Tests: duration adaptation
# ---------------------------------------------------------------------------

class TestDurationAdaptation:
    def test_source_longer_than_required_is_trimmed(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_category(tmp_path, "misc", n=1, duration_sec=10.0)
        ctx = _make_ctx(tmp_path, background_style="misc")
        prepare_background(ctx, required_duration_sec=3.0)
        actual = get_audio_duration(ctx.prepared_background())
        # Should be close to 3.0s, not 10.0s
        assert actual < 4.0

    def test_source_shorter_than_required_is_looped(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_category(tmp_path, "misc", n=1, duration_sec=2.0)
        ctx = _make_ctx(tmp_path, background_style="misc")
        prepare_background(ctx, required_duration_sec=5.0)
        actual = get_audio_duration(ctx.prepared_background())
        assert actual >= 5.0 - (1.0 / 30.0)

    def test_prepared_duration_at_least_required(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_category(tmp_path, "misc", n=1, duration_sec=4.0)
        ctx = _make_ctx(tmp_path, background_style="misc")
        prepare_background(ctx, required_duration_sec=3.0)
        actual = get_audio_duration(ctx.prepared_background())
        assert actual >= 3.0 - (1.0 / 30.0)


# ---------------------------------------------------------------------------
# Tests: output format and path
# ---------------------------------------------------------------------------

class TestOutputFormat:
    def test_output_file_exists_at_canonical_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_category(tmp_path, "misc", n=1, duration_sec=5.0)
        ctx = _make_ctx(tmp_path, background_style="misc")
        result = prepare_background(ctx, required_duration_sec=3.0)
        assert result == ctx.prepared_background()
        assert result.exists()

    def test_output_is_mp4(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_category(tmp_path, "misc", n=1, duration_sec=5.0)
        ctx = _make_ctx(tmp_path, background_style="misc")
        result = prepare_background(ctx, required_duration_sec=3.0)
        assert result.suffix == ".mp4"
