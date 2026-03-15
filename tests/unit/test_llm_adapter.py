"""Unit tests for T-007: LLM adapter interface and prompt loading."""
from __future__ import annotations

from typing import Any

import pytest

from app.adapters.llm_adapter import (
    ScriptGenerationError,
    ScriptGenerator,
    load_system_prompt,
    load_user_prompt,
)
from app.core.contracts import ValidatedJob


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


class TestPromptLoading:
    def test_system_prompt_loads_without_error(self):
        prompt = load_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_system_prompt_contains_json_requirement(self):
        prompt = load_system_prompt()
        assert "JSON" in prompt

    def test_system_prompt_contains_alternation_rule(self):
        prompt = load_system_prompt()
        assert "alternate" in prompt.lower() or "alternating" in prompt.lower() or "Speakers" in prompt

    def test_user_prompt_substitutes_topic(self):
        job = _make_job(topic="explique juros compostos")
        rendered = load_user_prompt(job)
        assert "explique juros compostos" in rendered

    def test_user_prompt_substitutes_duration(self):
        job = _make_job(duration_target_sec=25)
        rendered = load_user_prompt(job)
        assert "25" in rendered

    def test_user_prompt_substitutes_characters(self):
        job = _make_job(characters=["char_a", "char_b"])
        rendered = load_user_prompt(job)
        assert "char_a" in rendered
        assert "char_b" in rendered

    def test_user_prompt_char_order_matches_characters(self):
        job = _make_job(characters=["char_a", "char_b"])
        rendered = load_user_prompt(job)
        first_pos = rendered.index("char_a")
        second_pos = rendered.index("char_b")
        assert first_pos < second_pos


class TestScriptGeneratorInterface:
    def test_cannot_instantiate_abstract_class(self):
        with pytest.raises(TypeError):
            ScriptGenerator()  # type: ignore[abstract]

    def test_concrete_subclass_must_implement_generate(self):
        class IncompleteGenerator(ScriptGenerator):
            pass

        with pytest.raises(TypeError):
            IncompleteGenerator()  # type: ignore[abstract]

    def test_concrete_subclass_with_generate_is_instantiable(self):
        class StubGenerator(ScriptGenerator):
            def generate(self, system_prompt, user_prompt, job):
                return {"title_hook": "test", "dialogue": []}

        g = StubGenerator()
        assert isinstance(g, ScriptGenerator)

    def test_generate_signature_accepts_expected_args(self):
        class StubGenerator(ScriptGenerator):
            def generate(self, system_prompt, user_prompt, job):
                return {"title_hook": "test", "dialogue": []}

        g = StubGenerator()
        job = _make_job()
        result = g.generate("sys", "usr", job)
        assert "title_hook" in result
        assert "dialogue" in result

    def test_script_generation_error_is_exception(self):
        with pytest.raises(ScriptGenerationError):
            raise ScriptGenerationError("provider failed")
