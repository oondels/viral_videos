"""Unit tests for T-008: script writer module."""
from __future__ import annotations

import json
from typing import Any

import pytest

from app.adapters.llm_adapter import ScriptGenerationError, ScriptGenerator
from app.core.contracts import ValidatedJob
from app.core.job_context import JobContext
from app.modules.script_writer import write_script
from app.services.file_service import init_workspace


def _make_job(**kwargs: Any) -> ValidatedJob:
    defaults = dict(
        job_id="job_2026_03_15_001",
        topic="Por que gatos empurram objetos das mesas?",
        duration_target_sec=30,
        characters=["char_a", "char_b"],
        background_style="auto",
        output_preset="shorts_default",
    )
    defaults.update(kwargs)
    return ValidatedJob(**defaults)


def _make_ctx(tmp_path, job_id: str = "job_2026_03_15_001") -> JobContext:
    import os
    os.chdir(tmp_path)
    job = _make_job(job_id=job_id)
    ctx = JobContext(job=job)
    init_workspace(ctx)
    return ctx


def _valid_dialogue(chars: list[str], n: int = 6) -> list[dict[str, Any]]:
    """Generate a valid alternating dialogue with n lines."""
    return [
        {"index": i + 1, "speaker": chars[i % 2], "text": f"Line {i + 1} spoken text."}
        for i in range(n)
    ]


class StubGenerator(ScriptGenerator):
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def generate(self, system_prompt, user_prompt, job) -> dict[str, Any]:
        return self._payload


class TestWriteScriptSuccess:
    def test_writes_script_json(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _valid_dialogue(ctx.job.characters, n=6)
        gen = StubGenerator({"title_hook": "Why cats push things", "dialogue": dialogue})
        write_script(ctx, gen)
        assert ctx.script_json().exists()

    def test_writes_dialogue_json(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _valid_dialogue(ctx.job.characters, n=6)
        gen = StubGenerator({"title_hook": "Why cats push things", "dialogue": dialogue})
        write_script(ctx, gen)
        assert ctx.dialogue_json().exists()

    def test_script_json_contains_required_fields(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _valid_dialogue(ctx.job.characters, n=6)
        gen = StubGenerator({"title_hook": "Why cats push things", "dialogue": dialogue})
        write_script(ctx, gen)
        data = json.loads(ctx.script_json().read_text())
        assert data["job_id"] == ctx.job.job_id
        assert data["topic"] == ctx.job.topic
        assert "title_hook" in data
        assert "dialogue" in data

    def test_dialogue_json_matches_script_dialogue(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _valid_dialogue(ctx.job.characters, n=8)
        gen = StubGenerator({"title_hook": "Cats and gravity", "dialogue": dialogue})
        write_script(ctx, gen)
        script_data = json.loads(ctx.script_json().read_text())
        dialogue_data = json.loads(ctx.dialogue_json().read_text())
        assert dialogue_data == script_data["dialogue"]

    def test_accepts_12_lines(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _valid_dialogue(ctx.job.characters, n=12)
        gen = StubGenerator({"title_hook": "Max lines", "dialogue": dialogue})
        result = write_script(ctx, gen)
        assert len(result["dialogue"]) == 12

    def test_title_hook_stripped(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _valid_dialogue(ctx.job.characters, n=6)
        gen = StubGenerator({"title_hook": "  Padded hook  ", "dialogue": dialogue})
        result = write_script(ctx, gen)
        assert result["title_hook"] == "Padded hook"


class TestValidationFailures:
    def test_rejects_fewer_than_6_lines(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _valid_dialogue(ctx.job.characters, n=5)
        gen = StubGenerator({"title_hook": "Too short", "dialogue": dialogue})
        with pytest.raises(ScriptGenerationError, match="between 6 and 12"):
            write_script(ctx, gen)

    def test_rejects_more_than_12_lines(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _valid_dialogue(ctx.job.characters, n=13)
        gen = StubGenerator({"title_hook": "Too long", "dialogue": dialogue})
        with pytest.raises(ScriptGenerationError, match="between 6 and 12"):
            write_script(ctx, gen)

    def test_rejects_repeated_speakers(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _valid_dialogue(ctx.job.characters, n=6)
        # Make two consecutive lines use the same speaker
        dialogue[2]["speaker"] = dialogue[1]["speaker"]
        gen = StubGenerator({"title_hook": "Bad alternation", "dialogue": dialogue})
        with pytest.raises(ScriptGenerationError, match="repeats the previous speaker"):
            write_script(ctx, gen)

    def test_rejects_empty_text(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _valid_dialogue(ctx.job.characters, n=6)
        dialogue[3]["text"] = "   "
        gen = StubGenerator({"title_hook": "Empty text", "dialogue": dialogue})
        with pytest.raises(ScriptGenerationError, match="text is empty"):
            write_script(ctx, gen)

    def test_rejects_empty_title_hook(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _valid_dialogue(ctx.job.characters, n=6)
        gen = StubGenerator({"title_hook": "", "dialogue": dialogue})
        with pytest.raises(ScriptGenerationError, match="title_hook is missing or empty"):
            write_script(ctx, gen)

    def test_rejects_title_hook_too_long(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _valid_dialogue(ctx.job.characters, n=6)
        gen = StubGenerator({"title_hook": "x" * 80, "dialogue": dialogue})
        with pytest.raises(ScriptGenerationError, match="under 80 characters"):
            write_script(ctx, gen)

    def test_rejects_unknown_speaker(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _valid_dialogue(ctx.job.characters, n=6)
        dialogue[0]["speaker"] = "unknown_char"
        gen = StubGenerator({"title_hook": "Bad speaker", "dialogue": dialogue})
        with pytest.raises(ScriptGenerationError, match="not in job.characters"):
            write_script(ctx, gen)

    def test_rejects_wrong_index(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        dialogue = _valid_dialogue(ctx.job.characters, n=6)
        dialogue[0]["index"] = 99
        gen = StubGenerator({"title_hook": "Bad index", "dialogue": dialogue})
        with pytest.raises(ScriptGenerationError, match="index must be 1"):
            write_script(ctx, gen)

    def test_rejects_missing_dialogue(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx(tmp_path)
        gen = StubGenerator({"title_hook": "No dialogue"})
        with pytest.raises(ScriptGenerationError, match="dialogue must be a list"):
            write_script(ctx, gen)
