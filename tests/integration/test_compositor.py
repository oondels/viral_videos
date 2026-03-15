"""Integration tests for T-018: final video composition."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from app.core.contracts import ValidatedJob
from app.core.job_context import JobContext
from app.modules.compositor import CompositorError, compose_video
from app.services.file_service import init_workspace
from app.utils.audio_utils import write_silence_wav
from app.utils.ffprobe_utils import get_media_duration, get_video_dimensions
from app.utils.video_utils import make_color_video


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------

SEG_DURATION = 0.5  # seconds per dialogue line (keep tests fast)
N_LINES = 4


def _make_job(**kwargs: Any) -> ValidatedJob:
    defaults = dict(
        job_id="job_2026_03_15_018",
        topic="test topic",
        duration_target_sec=30,
        characters=["char_a", "char_b"],
        background_style="auto",
        output_preset="shorts_default",
    )
    defaults.update(kwargs)
    return ValidatedJob(**defaults)


def _make_ctx(tmp_path: Path) -> JobContext:
    import os
    os.chdir(tmp_path)
    job = _make_job()
    ctx = JobContext(job=job)
    init_workspace(ctx)
    return ctx


def _make_minimal_png(path: Path) -> None:
    import struct, zlib
    def _chunk(name: bytes, data: bytes) -> bytes:
        c = struct.pack(">I", len(data)) + name + data
        return c + struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)
    header = b"\x89PNG\r\n\x1a\n"
    ihdr = _chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = _chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00"))
    iend = _chunk(b"IEND", b"")
    path.write_bytes(header + ihdr + idat + iend)


def _setup_all_artifacts(tmp_path: Path, ctx: JobContext) -> None:
    """Build every artifact required by compose_video() using test stubs."""
    # Characters
    for char_id in ("char_a", "char_b"):
        char_dir = tmp_path / "assets" / "characters" / char_id
        char_dir.mkdir(parents=True, exist_ok=True)
        _make_minimal_png(char_dir / "base.png")
        (char_dir / "metadata.json").write_text(
            json.dumps({"character_id": char_id, "display_name": char_id}),
            encoding="utf-8",
        )

    # Font (copy from real assets — already committed)
    import os
    real_font = Path("assets/fonts/LiberationSans-Bold.ttf")
    font_dir = tmp_path / "assets" / "fonts"
    font_dir.mkdir(parents=True, exist_ok=True)
    import shutil
    if real_font.exists():
        shutil.copy(real_font, font_dir / real_font.name)
    else:
        # Fallback: write stub (subtitles may not render perfectly)
        (font_dir / "LiberationSans-Bold.ttf").write_bytes(b"\x00\x01\x00\x00")

    # Preset
    preset_dir = tmp_path / "assets" / "presets"
    preset_dir.mkdir(parents=True, exist_ok=True)
    preset = {
        "name": "shorts_default",
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "title_box": {"x": 0, "y": 80, "w": 1080, "h": 140},
        "title_timing": {"start_sec": 0.0, "end_sec": 1.0},
        "title_style": {
            "font": "LiberationSans-Bold.ttf",
            "font_size": 48,
            "color": "white",
            "stroke_color": "black",
            "stroke_width": 2,
            "align": "center",
        },
        "active_speaker_box": {"x": 40, "y": 300, "w": 400, "h": 600},
        "inactive_speaker_box": {"x": 640, "y": 380, "w": 400, "h": 600},
        "subtitle_safe_area": {"x": 40, "y": 1580, "w": 1000, "h": 280},
        "subtitle_style": {
            "font": "LiberationSans-Bold.ttf",
            "font_size": 48,
            "color": "white",
            "stroke_color": "black",
            "stroke_width": 3,
            "align": "center",
        },
    }
    (preset_dir / "shorts_default.json").write_text(
        json.dumps(preset), encoding="utf-8"
    )

    total = N_LINES * SEG_DURATION
    characters = ["char_a", "char_b"]

    # Audio segments
    for i in range(N_LINES):
        idx = i + 1
        speaker = characters[i % 2]
        seg = ctx.audio_segment(idx, speaker)
        write_silence_wav(seg, duration_sec=SEG_DURATION)

    # master_audio.wav
    ctx.audio_master_dir().mkdir(parents=True, exist_ok=True)
    write_silence_wav(ctx.master_audio(), duration_sec=total)

    # Clips (black video matching segment duration)
    ctx.clips_dir().mkdir(parents=True, exist_ok=True)
    for i in range(N_LINES):
        idx = i + 1
        speaker = characters[i % 2]
        make_color_video(ctx.clip(idx, speaker), duration_sec=SEG_DURATION, width=400, height=600)

    # Background
    ctx.background_dir().mkdir(parents=True, exist_ok=True)
    make_color_video(ctx.prepared_background(), duration_sec=total, width=1080, height=1920)

    # Timeline
    cursor = 0.0
    timeline = []
    for i in range(N_LINES):
        idx = i + 1
        speaker = characters[i % 2]
        start = round(cursor, 4)
        end = round(cursor + SEG_DURATION, 4)
        timeline.append({
            "index": idx,
            "speaker": speaker,
            "text": f"Line {idx}.",
            "start_sec": start,
            "end_sec": end,
            "duration_sec": round(end - start, 4),
            "audio_file": str(ctx.audio_segment(idx, speaker)),
            "clip_file": str(ctx.clip(idx, speaker)),
        })
        cursor = end
    ctx.script_dir().mkdir(parents=True, exist_ok=True)
    ctx.timeline_json().write_text(json.dumps(timeline), encoding="utf-8")

    # Script
    ctx.script_json().write_text(
        json.dumps({"title_hook": "Test Hook!", "dialogue": []}),
        encoding="utf-8",
    )

    # Subtitles (write directly, no module dependency)
    ctx.subtitles_dir().mkdir(parents=True, exist_ok=True)
    cues = []
    for i, item in enumerate(timeline, start=1):
        def _ts(sec: float) -> str:
            ms = round(sec * 1000)
            s, ms = divmod(ms, 1000)
            m, s = divmod(s, 60)
            h, m = divmod(m, 60)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
        cues.append(f"{i}\n{_ts(item['start_sec'])} --> {_ts(item['end_sec'])}\n{item['text']}")
    ctx.subtitles_srt().write_text("\n\n".join(cues) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestComposeVideo:
    def test_final_mp4_exists(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _setup_all_artifacts(tmp_path, ctx)
        compose_video(ctx)
        assert ctx.final_mp4().exists()

    def test_final_video_is_1080x1920(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _setup_all_artifacts(tmp_path, ctx)
        compose_video(ctx)
        w, h = get_video_dimensions(ctx.final_mp4())
        assert w == 1080
        assert h == 1920

    def test_final_duration_within_tolerance(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _setup_all_artifacts(tmp_path, ctx)
        compose_video(ctx)
        expected = N_LINES * SEG_DURATION
        actual = get_media_duration(ctx.final_mp4())
        assert abs(actual - expected) <= 0.10

    def test_render_metadata_json_exists(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _setup_all_artifacts(tmp_path, ctx)
        compose_video(ctx)
        assert ctx.render_metadata().exists()

    def test_render_metadata_has_required_fields(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _setup_all_artifacts(tmp_path, ctx)
        compose_video(ctx)
        meta = json.loads(ctx.render_metadata().read_text())
        required = {
            "job_id", "output_file", "duration_sec",
            "preset_name", "background_file", "subtitle_file",
            "timeline_item_count",
        }
        assert required.issubset(meta.keys())

    def test_render_metadata_job_id_matches(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _setup_all_artifacts(tmp_path, ctx)
        compose_video(ctx)
        meta = json.loads(ctx.render_metadata().read_text())
        assert meta["job_id"] == ctx.job.job_id

    def test_render_metadata_timeline_count_matches(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _setup_all_artifacts(tmp_path, ctx)
        compose_video(ctx)
        meta = json.loads(ctx.render_metadata().read_text())
        assert meta["timeline_item_count"] == N_LINES


class TestComposeVideoFailures:
    def test_missing_background_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _setup_all_artifacts(tmp_path, ctx)
        ctx.prepared_background().unlink()
        with pytest.raises(CompositorError, match="missing"):
            compose_video(ctx)

    def test_missing_clip_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _setup_all_artifacts(tmp_path, ctx)
        # Remove first clip
        clip = ctx.clip(1, "char_a")
        clip.unlink()
        with pytest.raises(CompositorError):
            compose_video(ctx)
