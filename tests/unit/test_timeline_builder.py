"""Unit tests for T-011: master audio concatenation and timeline persistence."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.core.contracts import ValidatedJob
from app.core.job_context import JobContext
from app.modules.timeline_builder import TimelineError, build_timeline
from app.services.file_service import init_workspace
from app.utils.audio_utils import write_silence_wav


def _make_job(**kwargs: Any) -> ValidatedJob:
    defaults = dict(
        job_id="job_2026_03_15_011",
        topic="test topic",
        duration_target_sec=30,
        characters=["char_a", "char_b"],
        background_style="auto",
        output_preset="shorts_default",
    )
    defaults.update(kwargs)
    return ValidatedJob(**defaults)


def _make_ctx(tmp_path: Path, job_id: str = "job_2026_03_15_011") -> JobContext:
    import os

    os.chdir(tmp_path)
    job = _make_job(job_id=job_id)
    ctx = JobContext(job=job)
    init_workspace(ctx)
    return ctx


def _build_manifest(
    ctx: JobContext,
    n: int = 6,
    duration_sec: float = 1.0,
) -> list[dict[str, Any]]:
    """Write silence WAV files and a manifest.json, return the manifest list."""
    characters = ["char_a", "char_b"]
    manifest = []
    for i in range(n):
        idx = i + 1
        speaker = characters[i % 2]
        seg_path = ctx.audio_segment(idx, speaker)
        write_silence_wav(seg_path, duration_sec=duration_sec)
        manifest.append(
            {
                "index": idx,
                "speaker": speaker,
                "text": f"Line {idx} text.",
                "voice_id": f"v_{speaker[-1]}",
                "audio_file": str(seg_path),
                "duration_sec": round(duration_sec, 4),
            }
        )
    ctx.audio_manifest().write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


class TestBuildTimelineSuccess:
    def test_produces_correct_item_count(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _build_manifest(ctx, n=6)
        timeline = build_timeline(ctx)
        assert len(timeline) == 6

    def test_first_item_starts_at_zero(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _build_manifest(ctx, n=4)
        timeline = build_timeline(ctx)
        assert timeline[0]["start_sec"] == 0.0

    def test_no_gaps_between_consecutive_items(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _build_manifest(ctx, n=6)
        timeline = build_timeline(ctx)
        for i in range(len(timeline) - 1):
            assert timeline[i]["end_sec"] == timeline[i + 1]["start_sec"], (
                f"Gap between item {i} and {i + 1}"
            )

    def test_last_end_sec_matches_master_duration(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _build_manifest(ctx, n=4, duration_sec=1.0)
        timeline = build_timeline(ctx)
        from app.utils.ffprobe_utils import get_audio_duration

        master_dur = get_audio_duration(ctx.master_audio())
        assert abs(timeline[-1]["end_sec"] - master_dur) <= 0.05

    def test_audio_file_matches_manifest(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        manifest = _build_manifest(ctx, n=6)
        timeline = build_timeline(ctx)
        for item, mf in zip(timeline, manifest):
            assert item["audio_file"] == mf["audio_file"]

    def test_clip_file_is_null_for_all_items(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _build_manifest(ctx, n=6)
        timeline = build_timeline(ctx)
        for item in timeline:
            assert item["clip_file"] is None

    def test_timeline_json_written_to_disk(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _build_manifest(ctx, n=4)
        build_timeline(ctx)
        assert ctx.timeline_json().exists()

    def test_return_value_matches_disk(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _build_manifest(ctx, n=4)
        timeline = build_timeline(ctx)
        on_disk = json.loads(ctx.timeline_json().read_text())
        assert on_disk == timeline

    def test_master_audio_written_to_disk(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _build_manifest(ctx, n=4)
        build_timeline(ctx)
        assert ctx.master_audio().exists()

    def test_indexes_are_contiguous_from_one(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _build_manifest(ctx, n=6)
        timeline = build_timeline(ctx)
        for i, item in enumerate(timeline, start=1):
            assert item["index"] == i

    def test_required_fields_present(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _build_manifest(ctx, n=4)
        timeline = build_timeline(ctx)
        required = {
            "index", "speaker", "text",
            "start_sec", "end_sec", "duration_sec",
            "audio_file", "clip_file",
        }
        for item in timeline:
            assert required.issubset(item.keys()), f"Missing fields in {item}"

    def test_duration_sec_equals_end_minus_start(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _build_manifest(ctx, n=6)
        timeline = build_timeline(ctx)
        for item in timeline:
            expected = round(item["end_sec"] - item["start_sec"], 6)
            assert abs(item["duration_sec"] - expected) < 1e-9


class TestBuildTimelineFailures:
    def test_empty_manifest_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        ctx.audio_manifest().write_text("[]", encoding="utf-8")
        with pytest.raises(TimelineError, match="empty"):
            build_timeline(ctx)

    def test_missing_segment_file_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        manifest = _build_manifest(ctx, n=4)
        # Delete one segment file
        Path(manifest[2]["audio_file"]).unlink()
        with pytest.raises(TimelineError, match="missing"):
            build_timeline(ctx)
