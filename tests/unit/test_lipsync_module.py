"""Unit tests for T-015: per-line talking-head clip generation and timeline update."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from app.adapters.lipsync_engine_adapter import LipSyncEngine, LipSyncError
from app.core.contracts import ValidatedJob
from app.core.job_context import JobContext
from app.modules.lipsync import generate_lipsync
from app.services.file_service import init_workspace
from app.utils.audio_utils import write_silence_wav
from app.utils.ffprobe_utils import get_audio_duration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_job(**kwargs: Any) -> ValidatedJob:
    defaults = dict(
        job_id="job_2026_03_15_015",
        topic="test topic",
        duration_target_sec=30,
        characters=["char_a", "char_b"],
        background_style="auto",
        output_preset="shorts_default",
    )
    defaults.update(kwargs)
    return ValidatedJob(**defaults)


def _make_ctx(tmp_path: Path, job_id: str = "job_2026_03_15_015") -> JobContext:
    import os

    os.chdir(tmp_path)
    job = _make_job(job_id=job_id)
    ctx = JobContext(job=job)
    init_workspace(ctx)
    return ctx


def _setup_characters(tmp_path: Path) -> None:
    """Create minimal character assets under tmp_path/assets/characters/."""
    for char_id in ("char_a", "char_b"):
        char_dir = tmp_path / "assets" / "characters" / char_id
        char_dir.mkdir(parents=True, exist_ok=True)
        _make_placeholder_png(char_dir / "base.png")
        (char_dir / "metadata.json").write_text(
            json.dumps({"character_id": char_id, "display_name": char_id}),
            encoding="utf-8",
        )


def _make_placeholder_png(path: Path) -> None:
    """Write a minimal 1x1 black PNG."""
    # Minimal valid PNG bytes (1x1 black pixel)
    import struct, zlib
    def _chunk(name: bytes, data: bytes) -> bytes:
        c = struct.pack(">I", len(data)) + name + data
        return c + struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)

    header = b"\x89PNG\r\n\x1a\n"
    ihdr = _chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat_data = zlib.compress(b"\x00\x00\x00\x00")
    idat = _chunk(b"IDAT", idat_data)
    iend = _chunk(b"IEND", b"")
    path.write_bytes(header + ihdr + idat + iend)


def _build_timeline(
    ctx: JobContext,
    n: int = 4,
    duration_sec: float = 0.5,
) -> list[dict[str, Any]]:
    """Write silence WAV segments and a timeline.json, return the timeline."""
    characters = ["char_a", "char_b"]
    timeline = []
    cursor = 0.0
    for i in range(n):
        idx = i + 1
        speaker = characters[i % 2]
        seg_path = ctx.audio_segment(idx, speaker)
        write_silence_wav(seg_path, duration_sec=duration_sec)
        start = round(cursor, 4)
        end = round(cursor + duration_sec, 4)
        timeline.append(
            {
                "index": idx,
                "speaker": speaker,
                "text": f"Line {idx}.",
                "start_sec": start,
                "end_sec": end,
                "duration_sec": round(end - start, 4),
                "audio_file": str(seg_path),
                "clip_file": None,
            }
        )
        cursor = end
    ctx.timeline_json().parent.mkdir(parents=True, exist_ok=True)
    ctx.timeline_json().write_text(
        json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return timeline


# ---------------------------------------------------------------------------
# Engine stubs
# ---------------------------------------------------------------------------

class BlackClipEngine(LipSyncEngine):
    """Stub engine that generates a real black video matching the audio duration."""

    def generate(self, image_path: Path, audio_path: Path, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "color=c=black:s=400x600:r=30",
                "-i", str(audio_path),
                "-c:v", "libx264", "-c:a", "aac",
                "-shortest",
                str(output_path),
            ],
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise LipSyncError(
                f"FFmpeg failed: {result.stderr.decode(errors='replace').strip()}"
            )
        return output_path


class FailingEngine(LipSyncEngine):
    """Engine that always raises LipSyncError."""

    def generate(self, image_path: Path, audio_path: Path, output_path: Path) -> Path:
        raise LipSyncError("engine error")


class NonWritingEngine(LipSyncEngine):
    """Engine that succeeds but does not write the output file."""

    def generate(self, image_path: Path, audio_path: Path, output_path: Path) -> Path:
        return output_path  # deliberately does not write


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGenerateLipSyncSuccess:
    def test_produces_one_clip_per_timeline_item(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _setup_characters(tmp_path)
        timeline = _build_timeline(ctx, n=4)
        generate_lipsync(ctx, BlackClipEngine())
        for item in timeline:
            assert ctx.clip(item["index"], item["speaker"]).exists()

    def test_clip_filenames_follow_naming_convention(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _setup_characters(tmp_path)
        timeline = _build_timeline(ctx, n=4)
        generate_lipsync(ctx, BlackClipEngine())
        for item in timeline:
            clip = ctx.clip(item["index"], item["speaker"])
            assert clip.name == f"{item['index']:03d}_{item['speaker']}_talk.mp4"

    def test_clip_file_updated_in_timeline(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _setup_characters(tmp_path)
        _build_timeline(ctx, n=4)
        updated = generate_lipsync(ctx, BlackClipEngine())
        for item in updated:
            assert item["clip_file"] is not None
            assert Path(item["clip_file"]).exists()

    def test_no_other_timeline_fields_are_changed(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _setup_characters(tmp_path)
        original = _build_timeline(ctx, n=4)
        updated = generate_lipsync(ctx, BlackClipEngine())
        for orig, upd in zip(original, updated):
            assert upd["index"] == orig["index"]
            assert upd["speaker"] == orig["speaker"]
            assert upd["text"] == orig["text"]
            assert upd["start_sec"] == orig["start_sec"]
            assert upd["end_sec"] == orig["end_sec"]
            assert upd["duration_sec"] == orig["duration_sec"]
            assert upd["audio_file"] == orig["audio_file"]

    def test_timeline_json_on_disk_updated(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _setup_characters(tmp_path)
        _build_timeline(ctx, n=4)
        updated = generate_lipsync(ctx, BlackClipEngine())
        on_disk = json.loads(ctx.timeline_json().read_text())
        assert on_disk == updated

    def test_return_value_count_matches_timeline(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _setup_characters(tmp_path)
        _build_timeline(ctx, n=6)
        updated = generate_lipsync(ctx, BlackClipEngine())
        assert len(updated) == 6

    def test_clip_duration_within_tolerance(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _setup_characters(tmp_path)
        _build_timeline(ctx, n=2, duration_sec=1.0)
        updated = generate_lipsync(ctx, BlackClipEngine())
        for item in updated:
            clip_dur = get_audio_duration(Path(item["clip_file"]))
            assert abs(clip_dur - item["duration_sec"]) <= 0.10


class TestGenerateLipSyncFailures:
    def test_missing_character_asset_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        # Do NOT set up characters
        _build_timeline(ctx, n=2)
        from app.services.asset_service import AssetError
        with pytest.raises(AssetError, match="missing"):
            generate_lipsync(ctx, BlackClipEngine())

    def test_engine_error_raises_lipsync_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _setup_characters(tmp_path)
        _build_timeline(ctx, n=2)
        with pytest.raises(LipSyncError, match="engine error"):
            generate_lipsync(ctx, FailingEngine())

    def test_non_writing_engine_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _setup_characters(tmp_path)
        _build_timeline(ctx, n=2)
        with pytest.raises(LipSyncError, match="did not produce clip"):
            generate_lipsync(ctx, NonWritingEngine())
