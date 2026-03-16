"""Unit tests for T-010: per-line audio generation and manifest persistence."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.adapters.tts_provider_adapter import TTSError, TTSProvider
from app.core.contracts import ValidatedJob
from app.core.job_context import JobContext
from app.modules.tts import generate_tts
from app.services.file_service import init_workspace
from app.utils.audio_utils import write_silence_wav


def _make_job(**kwargs: Any) -> ValidatedJob:
    defaults = dict(
        job_id="job_2026_03_15_010",
        topic="test topic",
        duration_target_sec=30,
        characters=["char_a", "char_b"],
        background_style="auto",
        output_preset="shorts_default",
    )
    defaults.update(kwargs)
    return ValidatedJob(**defaults)


def _make_ctx(tmp_path: Path, job_id: str = "job_2026_03_15_010") -> JobContext:
    import os

    os.chdir(tmp_path)
    job = _make_job(job_id=job_id)
    ctx = JobContext(job=job)
    init_workspace(ctx)
    return ctx


def _make_dialogue(chars: list[str], n: int = 6) -> list[dict[str, Any]]:
    return [
        {"index": i + 1, "speaker": chars[i % 2], "text": f"Line {i + 1} text."}
        for i in range(n)
    ]


def _write_dialogue(ctx: JobContext, dialogue: list[dict[str, Any]]) -> None:
    ctx.dialogue_json().write_text(
        json.dumps(dialogue, ensure_ascii=False), encoding="utf-8"
    )


class SilenceProvider(TTSProvider):
    """Stub provider that writes a silent WAV file of fixed duration."""

    def __init__(self, duration_sec: float = 1.0) -> None:
        self._duration = duration_sec

    def synthesize(self, text: str, voice_id: str, output_path: Path) -> None:
        write_silence_wav(output_path, duration_sec=self._duration)


class FailingProvider(TTSProvider):
    """Stub provider that always raises TTSError."""

    def synthesize(self, text: str, voice_id: str, output_path: Path) -> None:
        raise TTSError("provider error")


class NonWritingProvider(TTSProvider):
    """Stub provider that succeeds but does not write the file."""

    def synthesize(self, text: str, voice_id: str, output_path: Path) -> None:
        pass  # deliberately does not write anything


VOICE_MAPPING = {"char_a": "v_a", "char_b": "v_b"}


class TestGenerateTTSSuccess:
    def test_creates_one_segment_per_line(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _make_dialogue(ctx.job.characters, n=6)
        _write_dialogue(ctx, dialogue)
        generate_tts(ctx, SilenceProvider(), VOICE_MAPPING)
        for line in dialogue:
            assert ctx.audio_segment(line["index"], line["speaker"]).exists()

    def test_segment_filenames_follow_naming_convention(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _make_dialogue(ctx.job.characters, n=6)
        _write_dialogue(ctx, dialogue)
        generate_tts(ctx, SilenceProvider(), VOICE_MAPPING)
        for line in dialogue:
            segment = ctx.audio_segment(line["index"], line["speaker"])
            assert segment.name == f"{line['index']:03d}_{line['speaker']}.mp3"

    def test_writes_manifest_json(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _make_dialogue(ctx.job.characters, n=6)
        _write_dialogue(ctx, dialogue)
        generate_tts(ctx, SilenceProvider(), VOICE_MAPPING)
        assert ctx.audio_manifest().exists()

    def test_manifest_has_correct_item_count(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        n = 8
        dialogue = _make_dialogue(ctx.job.characters, n=n)
        _write_dialogue(ctx, dialogue)
        manifest = generate_tts(ctx, SilenceProvider(), VOICE_MAPPING)
        assert len(manifest) == n

    def test_manifest_order_matches_dialogue(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _make_dialogue(ctx.job.characters, n=6)
        _write_dialogue(ctx, dialogue)
        manifest = generate_tts(ctx, SilenceProvider(), VOICE_MAPPING)
        for i, (item, line) in enumerate(zip(manifest, dialogue)):
            assert item["index"] == line["index"], f"manifest[{i}].index mismatch"
            assert item["speaker"] == line["speaker"]
            assert item["text"] == line["text"]

    def test_manifest_contains_required_fields(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _make_dialogue(ctx.job.characters, n=6)
        _write_dialogue(ctx, dialogue)
        manifest = generate_tts(ctx, SilenceProvider(), VOICE_MAPPING)
        required = {"index", "speaker", "text", "voice_id", "audio_file", "duration_sec"}
        for item in manifest:
            assert required.issubset(item.keys()), f"Missing fields in {item}"

    def test_manifest_audio_files_exist_on_disk(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _make_dialogue(ctx.job.characters, n=6)
        _write_dialogue(ctx, dialogue)
        manifest = generate_tts(ctx, SilenceProvider(), VOICE_MAPPING)
        for item in manifest:
            assert Path(item["audio_file"]).exists(), f"Missing: {item['audio_file']}"

    def test_duration_is_positive(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _make_dialogue(ctx.job.characters, n=6)
        _write_dialogue(ctx, dialogue)
        manifest = generate_tts(ctx, SilenceProvider(duration_sec=1.5), VOICE_MAPPING)
        for item in manifest:
            assert item["duration_sec"] > 0

    def test_manifest_json_on_disk_matches_return_value(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _make_dialogue(ctx.job.characters, n=6)
        _write_dialogue(ctx, dialogue)
        manifest = generate_tts(ctx, SilenceProvider(), VOICE_MAPPING)
        on_disk = json.loads(ctx.audio_manifest().read_text())
        assert on_disk == manifest

    def test_voice_id_in_manifest_matches_mapping(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _make_dialogue(ctx.job.characters, n=6)
        _write_dialogue(ctx, dialogue)
        manifest = generate_tts(ctx, SilenceProvider(), VOICE_MAPPING)
        for item in manifest:
            assert item["voice_id"] == VOICE_MAPPING[item["speaker"]]


class TestGenerateTTSFailures:
    def test_missing_voice_mapping_raises_before_synthesis(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _make_dialogue(ctx.job.characters, n=6)
        _write_dialogue(ctx, dialogue)
        partial_mapping = {"char_a": "v_a"}  # char_b missing
        with pytest.raises(TTSError, match="No voice mapping found"):
            generate_tts(ctx, SilenceProvider(), partial_mapping)

    def test_provider_error_raises_tts_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _make_dialogue(ctx.job.characters, n=6)
        _write_dialogue(ctx, dialogue)
        with pytest.raises(TTSError, match="provider error"):
            generate_tts(ctx, FailingProvider(), VOICE_MAPPING)

    def test_provider_not_writing_file_raises_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _make_dialogue(ctx.job.characters, n=6)
        _write_dialogue(ctx, dialogue)
        with pytest.raises(TTSError, match="did not write segment file"):
            generate_tts(ctx, NonWritingProvider(), VOICE_MAPPING)
