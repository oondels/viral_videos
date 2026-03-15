"""Unit tests for T-009: TTS provider adapter and voice mapping."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.adapters.tts_provider_adapter import (
    TTSError,
    TTSProvider,
    load_voice_mapping,
    resolve_voice_id,
)


class TestLoadVoiceMapping:
    def test_loads_valid_config(self, tmp_path):
        cfg = tmp_path / "voices.json"
        cfg.write_text(json.dumps({"char_a": "v_a", "char_b": "v_b"}))
        mapping = load_voice_mapping(cfg)
        assert mapping == {"char_a": "v_a", "char_b": "v_b"}

    def test_raises_if_file_missing(self, tmp_path):
        with pytest.raises(TTSError, match="Voice mapping config not found"):
            load_voice_mapping(tmp_path / "nonexistent.json")

    def test_raises_on_invalid_json(self, tmp_path):
        cfg = tmp_path / "voices.json"
        cfg.write_text("not json {{{")
        with pytest.raises(TTSError, match="Invalid JSON"):
            load_voice_mapping(cfg)

    def test_returns_dict(self, tmp_path):
        cfg = tmp_path / "voices.json"
        cfg.write_text(json.dumps({"char_a": "v_a"}))
        result = load_voice_mapping(cfg)
        assert isinstance(result, dict)

    def test_canonical_voices_json_loads(self, monkeypatch):
        """The committed config/voices.json must load without error."""
        monkeypatch.chdir(Path(__file__).parent.parent.parent)
        mapping = load_voice_mapping()
        assert "char_a" in mapping
        assert "char_b" in mapping


class TestResolveVoiceId:
    def test_returns_voice_id_for_known_character(self):
        mapping = {"char_a": "v_a", "char_b": "v_b"}
        assert resolve_voice_id("char_a", mapping) == "v_a"

    def test_raises_for_unknown_character(self):
        mapping = {"char_a": "v_a"}
        with pytest.raises(TTSError, match="No voice mapping found"):
            resolve_voice_id("char_unknown", mapping)

    def test_error_message_lists_known_characters(self):
        mapping = {"char_a": "v_a", "char_b": "v_b"}
        with pytest.raises(TTSError, match="char_a"):
            resolve_voice_id("ghost", mapping)


class TestTTSProviderInterface:
    def test_cannot_instantiate_abstract_class(self):
        with pytest.raises(TypeError):
            TTSProvider()  # type: ignore[abstract]

    def test_concrete_subclass_must_implement_synthesize(self):
        class Incomplete(TTSProvider):
            pass

        with pytest.raises(TypeError):
            Incomplete()  # type: ignore[abstract]

    def test_concrete_implementation_is_instantiable(self):
        class StubProvider(TTSProvider):
            def synthesize(self, text, voice_id, output_path):
                pass

        p = StubProvider()
        assert isinstance(p, TTSProvider)

    def test_synthesize_accepts_expected_signature(self, tmp_path):
        class StubProvider(TTSProvider):
            def synthesize(self, text, voice_id, output_path):
                output_path.write_bytes(b"fake_audio")

        p = StubProvider()
        out = tmp_path / "segment.wav"
        p.synthesize("hello", "v_a", out)
        assert out.exists()

    def test_tts_error_is_exception(self):
        with pytest.raises(TTSError):
            raise TTSError("provider failed")
