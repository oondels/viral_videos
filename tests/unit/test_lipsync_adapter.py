"""Unit tests for T-014: lip-sync engine adapter boundary."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.adapters.lipsync_engine_adapter import LipSyncEngine, LipSyncError


class ConcreteLipSyncEngine(LipSyncEngine):
    """Minimal concrete implementation for interface shape tests."""

    def generate(
        self,
        image_path: Path,
        audio_path: Path,
        output_path: Path,
    ) -> Path:
        output_path.write_bytes(b"\x00")
        return output_path


class FailingEngine(LipSyncEngine):
    """Engine that always raises LipSyncError."""

    def generate(
        self,
        image_path: Path,
        audio_path: Path,
        output_path: Path,
    ) -> Path:
        raise LipSyncError("engine failure")


class TestLipSyncEngineInterface:
    def test_abstract_class_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            LipSyncEngine()  # type: ignore[abstract]

    def test_concrete_subclass_can_be_instantiated(self):
        engine = ConcreteLipSyncEngine()
        assert isinstance(engine, LipSyncEngine)

    def test_generate_accepts_image_audio_and_output_paths(self, tmp_path):
        engine = ConcreteLipSyncEngine()
        image = tmp_path / "base.png"
        audio = tmp_path / "line.wav"
        output = tmp_path / "clip.mp4"
        image.write_bytes(b"\x89PNG")
        audio.write_bytes(b"RIFF")
        result = engine.generate(image, audio, output)
        assert result == output

    def test_generate_returns_output_path(self, tmp_path):
        engine = ConcreteLipSyncEngine()
        image = tmp_path / "base.png"
        audio = tmp_path / "line.wav"
        output = tmp_path / "clip.mp4"
        image.write_bytes(b"\x89PNG")
        audio.write_bytes(b"RIFF")
        returned = engine.generate(image, audio, output)
        assert returned is output or returned == output

    def test_lipsync_error_is_raised_by_failing_engine(self, tmp_path):
        engine = FailingEngine()
        with pytest.raises(LipSyncError, match="engine failure"):
            engine.generate(tmp_path / "a.png", tmp_path / "b.wav", tmp_path / "c.mp4")

    def test_subclass_without_generate_cannot_be_instantiated(self):
        class Incomplete(LipSyncEngine):
            pass

        with pytest.raises(TypeError):
            Incomplete()  # type: ignore[abstract]
