"""Unit tests for T-012: subtitle generation from timeline."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from app.core.contracts import ValidatedJob
from app.core.job_context import JobContext
from app.modules.subtitles import SubtitleError, generate_subtitles
from app.services.file_service import init_workspace


def _make_job(**kwargs: Any) -> ValidatedJob:
    defaults = dict(
        job_id="job_2026_03_15_012",
        topic="test topic",
        duration_target_sec=30,
        characters=["char_a", "char_b"],
        background_style="auto",
        output_preset="shorts_default",
    )
    defaults.update(kwargs)
    return ValidatedJob(**defaults)


def _make_ctx(tmp_path: Path, job_id: str = "job_2026_03_15_012") -> JobContext:
    import os

    os.chdir(tmp_path)
    job = _make_job(job_id=job_id)
    ctx = JobContext(job=job)
    init_workspace(ctx)
    return ctx


def _write_timeline(ctx: JobContext, items: list[dict[str, Any]]) -> None:
    ctx.timeline_json().parent.mkdir(parents=True, exist_ok=True)
    ctx.timeline_json().write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _make_timeline(n: int = 6, duration_sec: float = 1.0) -> list[dict[str, Any]]:
    characters = ["char_a", "char_b"]
    items = []
    cursor = 0.0
    for i in range(n):
        start = round(cursor, 4)
        end = round(cursor + duration_sec, 4)
        items.append(
            {
                "index": i + 1,
                "speaker": characters[i % 2],
                "text": f"Line {i + 1} text.",
                "start_sec": start,
                "end_sec": end,
                "duration_sec": round(end - start, 4),
                "audio_file": f"output/jobs/x/audio/segments/{i+1:03d}_char.mp3",
                "clip_file": None,
            }
        )
        cursor = end
    return items


def _parse_srt(content: str) -> list[dict]:
    """Parse SRT content into a list of cue dicts."""
    cues = []
    blocks = content.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 3:
            continue
        number = int(lines[0].strip())
        timing = lines[1].strip()
        text = "\n".join(lines[2:])
        cues.append({"number": number, "timing": timing, "text": text})
    return cues


class TestGenerateSubtitlesSuccess:
    def test_produces_correct_cue_count(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _write_timeline(ctx, _make_timeline(n=6))
        srt = generate_subtitles(ctx)
        cues = _parse_srt(srt)
        assert len(cues) == 6

    def test_first_cue_starts_at_zero(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _write_timeline(ctx, _make_timeline(n=4))
        srt = generate_subtitles(ctx)
        cues = _parse_srt(srt)
        assert cues[0]["timing"].startswith("00:00:00,000 -->")

    def test_cue_text_matches_timeline_exactly(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        timeline = _make_timeline(n=6)
        _write_timeline(ctx, timeline)
        srt = generate_subtitles(ctx)
        cues = _parse_srt(srt)
        for cue, item in zip(cues, timeline):
            assert cue["text"] == item["text"]

    def test_cue_numbering_starts_at_one_and_is_contiguous(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _write_timeline(ctx, _make_timeline(n=6))
        srt = generate_subtitles(ctx)
        cues = _parse_srt(srt)
        for i, cue in enumerate(cues, start=1):
            assert cue["number"] == i

    def test_srt_file_written_to_disk(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _write_timeline(ctx, _make_timeline(n=4))
        generate_subtitles(ctx)
        assert ctx.subtitles_srt().exists()

    def test_return_value_matches_disk(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _write_timeline(ctx, _make_timeline(n=4))
        srt = generate_subtitles(ctx)
        on_disk = ctx.subtitles_srt().read_text(encoding="utf-8")
        assert on_disk == srt

    def test_srt_timing_format_is_valid(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        _write_timeline(ctx, _make_timeline(n=4))
        srt = generate_subtitles(ctx)
        cues = _parse_srt(srt)
        pattern = re.compile(
            r"\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}"
        )
        for cue in cues:
            assert pattern.match(cue["timing"]), f"Invalid timing: {cue['timing']}"

    def test_consecutive_timings_are_gapless(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        timeline = _make_timeline(n=6, duration_sec=2.0)
        _write_timeline(ctx, timeline)
        srt = generate_subtitles(ctx)
        cues = _parse_srt(srt)
        for i in range(len(cues) - 1):
            end_of_prev = cues[i]["timing"].split(" --> ")[1]
            start_of_next = cues[i + 1]["timing"].split(" --> ")[0]
            assert end_of_prev == start_of_next


class TestGenerateSubtitlesFailures:
    def test_missing_timeline_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        with pytest.raises(SubtitleError, match="missing"):
            generate_subtitles(ctx)

    def test_unordered_timeline_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        timeline = _make_timeline(n=4)
        # Swap two items to break ordering
        timeline[1]["start_sec"], timeline[2]["start_sec"] = (
            timeline[2]["start_sec"],
            timeline[1]["start_sec"],
        )
        _write_timeline(ctx, timeline)
        with pytest.raises(SubtitleError, match="unordered"):
            generate_subtitles(ctx)

    def test_end_lte_start_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        timeline = _make_timeline(n=2)
        timeline[0]["end_sec"] = timeline[0]["start_sec"]  # end == start
        _write_timeline(ctx, timeline)
        with pytest.raises(SubtitleError, match="end.*<=.*start|<="):
            generate_subtitles(ctx)
