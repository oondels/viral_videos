"""Integration tests for T-019: full single-job pipeline end-to-end."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from app.adapters.lipsync_engine_adapter import LipSyncEngine, LipSyncError
from app.adapters.llm_adapter import ScriptGenerator, ScriptGenerationError
from app.adapters.tts_provider_adapter import TTSProvider
from app.pipeline import PipelineError, run_pipeline
from app.utils.audio_utils import write_silence_wav
from app.utils.video_utils import make_color_video


# ---------------------------------------------------------------------------
# Stub providers
# ---------------------------------------------------------------------------

class StubLLM(ScriptGenerator):
    """Returns a minimal valid script without calling any API."""

    def __init__(self, characters: list[str] | None = None) -> None:
        self._characters = characters or ["char_a", "char_b"]

    def generate(self, system_prompt: str, user_prompt: str, job: Any) -> dict[str, Any]:
        chars = self._characters
        lines = [
            {"index": 1, "speaker": chars[0], "text": "Hello there!"},
            {"index": 2, "speaker": chars[1], "text": "How are you?"},
            {"index": 3, "speaker": chars[0], "text": "I am great, thanks."},
            {"index": 4, "speaker": chars[1], "text": "That is awesome."},
            {"index": 5, "speaker": chars[0], "text": "Indeed it is."},
            {"index": 6, "speaker": chars[1], "text": "Totally agree!"},
        ]
        return {"title_hook": "Test Hook!", "dialogue": lines}


class StubTTS(TTSProvider):
    """Writes silent WAV files without calling any API."""

    def synthesize(self, text: str, voice_id: str, output_path: Path) -> None:
        write_silence_wav(output_path, duration_sec=0.5)


class StubLipSync(LipSyncEngine):
    """Generates a black video matching the audio duration."""

    def generate(self, image_path: Path, audio_path: Path, output_path: Path) -> Path:
        from app.utils.ffprobe_utils import get_media_duration
        dur = get_media_duration(audio_path)
        make_color_video(output_path, duration_sec=dur, width=400, height=600)
        return output_path


class FailingLipSync(LipSyncEngine):
    """Always fails."""

    def generate(self, image_path: Path, audio_path: Path, output_path: Path) -> Path:
        raise LipSyncError("stub engine failure")


class FailingLLM(ScriptGenerator):
    """Always fails."""

    def generate(self, system_prompt: str, user_prompt: str, job: Any) -> dict[str, Any]:
        raise ScriptGenerationError("LLM failure")


# ---------------------------------------------------------------------------
# Fixture setup helpers
# ---------------------------------------------------------------------------

def _setup_assets(tmp_path: Path) -> None:
    """Create minimum asset files needed by the pipeline."""
    import struct, zlib

    def _png(path: Path) -> None:
        def _chunk(name: bytes, data: bytes) -> bytes:
            c = struct.pack(">I", len(data)) + name + data
            return c + struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)
        path.write_bytes(
            b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
            + _chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00"))
            + _chunk(b"IEND", b"")
        )

    for char_id in ("char_a", "char_b"):
        char_dir = tmp_path / "assets" / "characters" / char_id
        char_dir.mkdir(parents=True, exist_ok=True)
        _png(char_dir / "base.png")
        (char_dir / "metadata.json").write_text(
            json.dumps({"character_id": char_id, "display_name": char_id})
        )

    font_dir = tmp_path / "assets" / "fonts"
    font_dir.mkdir(parents=True, exist_ok=True)
    real_font = Path("assets/fonts/LiberationSans-Bold.ttf")
    if real_font.exists():
        shutil.copy(real_font, font_dir / real_font.name)
    else:
        (font_dir / "LiberationSans-Bold.ttf").write_bytes(b"\x00\x01\x00\x00")

    preset_dir = tmp_path / "assets" / "presets"
    preset_dir.mkdir(parents=True, exist_ok=True)
    preset = {
        "name": "shorts_default",
        "width": 1080, "height": 1920, "fps": 30,
        "title_box": {"x": 0, "y": 80, "w": 1080, "h": 140},
        "title_timing": {"start_sec": 0.0, "end_sec": 1.0},
        "title_style": {
            "font": "LiberationSans-Bold.ttf", "font_size": 48,
            "color": "white", "stroke_color": "black", "stroke_width": 2, "align": "center",
        },
        "active_speaker_box": {"x": 40, "y": 300, "w": 400, "h": 600},
        "inactive_speaker_box": {"x": 640, "y": 380, "w": 400, "h": 600},
        "subtitle_safe_area": {"x": 40, "y": 1580, "w": 1000, "h": 280},
        "subtitle_style": {
            "font": "LiberationSans-Bold.ttf", "font_size": 48,
            "color": "white", "stroke_color": "black", "stroke_width": 3, "align": "center",
        },
        "speaker_transition_duration_sec": 0.15,
        "speaker_anchor": "center",
    }
    (preset_dir / "shorts_default.json").write_text(json.dumps(preset))

    # Background video (any category will do for auto selection)
    bg_dir = tmp_path / "assets" / "backgrounds" / "misc"
    bg_dir.mkdir(parents=True, exist_ok=True)
    make_color_video(bg_dir / "bg.mp4", duration_sec=5.0, width=640, height=480)


def _write_voice_config(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "voices.json").write_text(
        json.dumps({"char_a": "v_a", "char_b": "v_b"})
    )


def _write_job_file(tmp_path: Path) -> Path:
    job = {
        "topic": "explique inflação de forma engraçada",
        "duration_target_sec": 30,
        "background_style": "auto",
        "characters": ["char_a", "char_b"],
        "output_preset": "shorts_default",
    }
    job_file = tmp_path / "job_test.json"
    job_file.write_text(json.dumps(job))
    return job_file


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPipelineSuccess:
    def test_produces_final_mp4(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _write_voice_config(tmp_path)
        job_file = _write_job_file(tmp_path)
        ctx = run_pipeline(job_file, StubLLM(), StubTTS(), StubLipSync())
        assert ctx.final_mp4().exists()

    def test_all_canonical_artifacts_exist(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _write_voice_config(tmp_path)
        job_file = _write_job_file(tmp_path)
        ctx = run_pipeline(job_file, StubLLM(), StubTTS(), StubLipSync())
        assert ctx.script_json().exists()
        assert ctx.dialogue_json().exists()
        assert ctx.audio_manifest().exists()
        assert ctx.master_audio().exists()
        assert ctx.timeline_json().exists()
        assert ctx.prepared_background().exists()
        assert ctx.subtitles_srt().exists()
        assert ctx.final_mp4().exists()
        assert ctx.render_metadata().exists()
        assert ctx.job_log().exists()

    def test_stages_execute_in_canonical_order(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _write_voice_config(tmp_path)
        job_file = _write_job_file(tmp_path)
        ctx = run_pipeline(job_file, StubLLM(), StubTTS(), StubLipSync())
        log_entries = [
            json.loads(line) for line in ctx.job_log().read_text().splitlines()
        ]
        started = [e["stage"] for e in log_entries if e["event"] == "stage_started"]
        expected_order = [
            "init_job_workspace",
            "write_script", "generate_tts", "build_timeline", "generate_lipsync",
            "prepare_background", "generate_subtitles", "compose_video", "finalize_job",
        ]
        assert started == expected_order


class TestPipelineFailFast:
    def test_invalid_input_raises_pipeline_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _write_voice_config(tmp_path)
        bad_job = tmp_path / "bad.json"
        bad_job.write_text(json.dumps({"not_topic": "x"}))
        with pytest.raises(PipelineError, match="validate_input"):
            run_pipeline(bad_job, StubLLM(), StubTTS(), StubLipSync())

    def test_validation_failure_produces_no_workspace(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _write_voice_config(tmp_path)
        bad_job = tmp_path / "bad.json"
        bad_job.write_text(json.dumps({"topic": ""}))
        with pytest.raises(PipelineError):
            run_pipeline(bad_job, StubLLM(), StubTTS(), StubLipSync())
        # No output/jobs/ directory should be created
        assert not (tmp_path / "output" / "jobs").exists()

    def test_lipsync_failure_preserves_upstream_artifacts(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _write_voice_config(tmp_path)
        job_file = _write_job_file(tmp_path)
        with pytest.raises(PipelineError, match="generate_lipsync"):
            run_pipeline(job_file, StubLLM(), StubTTS(), FailingLipSync())
        # Script, audio, and timeline should still exist
        from app.core.contracts import validate_job
        raw = json.loads(job_file.read_text())
        from pathlib import Path as P
        from app.core.job_context import JobContext
        # Find any created job context by scanning output
        output_jobs = list((tmp_path / "output" / "jobs").iterdir())
        assert len(output_jobs) == 1
        job_dir = output_jobs[0]
        assert (job_dir / "script" / "script.json").exists()
        assert (job_dir / "script" / "dialogue.json").exists()
        assert (job_dir / "audio" / "manifest.json").exists()
        assert (job_dir / "script" / "timeline.json").exists()
        # Final video must NOT exist
        assert not (job_dir / "render" / "final.mp4").exists()

    def test_llm_failure_raises_pipeline_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _write_voice_config(tmp_path)
        job_file = _write_job_file(tmp_path)
        with pytest.raises(PipelineError, match="write_script"):
            run_pipeline(job_file, FailingLLM(), StubTTS(), StubLipSync())
