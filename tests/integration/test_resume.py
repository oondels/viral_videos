"""Integration tests for T-027: --resume mode pipeline."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from app.adapters.lipsync_engine_adapter import LipSyncEngine
from app.adapters.llm_adapter import ScriptGenerator
from app.adapters.tts_provider_adapter import TTSProvider
from app.pipeline import PipelineError, resume_pipeline, run_pipeline
from app.utils.audio_utils import write_silence_wav
from app.utils.video_utils import make_color_video


# ---------------------------------------------------------------------------
# Stub providers (same pattern as test_pipeline.py)
# ---------------------------------------------------------------------------

class StubLLM(ScriptGenerator):
    def generate(self, system_prompt: str, user_prompt: str, job: Any) -> dict[str, Any]:
        chars = ["char_a", "char_b"]
        lines = [
            {"index": 1, "speaker": chars[0], "text": "Hello there!"},
            {"index": 2, "speaker": chars[1], "text": "How are you?"},
            {"index": 3, "speaker": chars[0], "text": "I am great, thanks."},
            {"index": 4, "speaker": chars[1], "text": "That is awesome."},
            {"index": 5, "speaker": chars[0], "text": "Indeed it is."},
            {"index": 6, "speaker": chars[1], "text": "Totally agree!"},
        ]
        return {"title_hook": "Resume Test!", "dialogue": lines}


class StubTTS(TTSProvider):
    def synthesize(self, text: str, voice_id: str, output_path: Path) -> None:
        write_silence_wav(output_path, duration_sec=0.5)


class StubLipSync(LipSyncEngine):
    def generate(self, image_path: Path, audio_path: Path, output_path: Path) -> Path:
        from app.utils.ffprobe_utils import get_media_duration
        dur = get_media_duration(audio_path)
        make_color_video(output_path, duration_sec=dur, width=400, height=600)
        return output_path


# ---------------------------------------------------------------------------
# Asset / job setup helpers (copied from test_pipeline.py)
# ---------------------------------------------------------------------------

def _setup_assets(tmp_path: Path) -> None:
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
    }
    (preset_dir / "shorts_default.json").write_text(json.dumps(preset))

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
        "topic": "test resume topic",
        "duration_target_sec": 30,
        "background_style": "auto",
        "characters": ["char_a", "char_b"],
        "output_preset": "shorts_default",
    }
    job_file = tmp_path / "job_test.json"
    job_file.write_text(json.dumps(job))
    return job_file


def _run_full(tmp_path: Path):
    """Run a full pipeline and return the ctx."""
    _setup_assets(tmp_path)
    _write_voice_config(tmp_path)
    job_file = _write_job_file(tmp_path)
    return run_pipeline(job_file, StubLLM(), StubTTS(), StubLipSync())


# ---------------------------------------------------------------------------
# Tests: init_workspace persistence
# ---------------------------------------------------------------------------

class TestJobInputPersistence:
    def test_job_input_json_created_by_init_workspace(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _run_full(tmp_path)
        job_input = ctx.root() / "job_input.json"
        assert job_input.exists(), "job_input.json must be created by init_workspace"

    def test_job_input_json_is_valid_json(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _run_full(tmp_path)
        data = json.loads((ctx.root() / "job_input.json").read_text())
        assert data["topic"] == "test resume topic"
        assert data["job_id"] == ctx.job.job_id

    def test_job_input_json_contains_required_fields(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _run_full(tmp_path)
        data = json.loads((ctx.root() / "job_input.json").read_text())
        for field in ("job_id", "topic", "duration_target_sec", "characters", "output_preset"):
            assert field in data, f"job_input.json must contain field '{field}'"


# ---------------------------------------------------------------------------
# Tests: resume_pipeline skipping behaviour
# ---------------------------------------------------------------------------

class TestResumePipelineSkips:
    def test_resume_skips_all_stages_when_all_artifacts_present(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _run_full(tmp_path)
        job_id = ctx.job.job_id

        # Resume with everything intact — all stages should be skipped
        ctx2 = resume_pipeline(job_id, StubLLM(), StubTTS(), StubLipSync())

        log_entries = [
            json.loads(line) for line in ctx2.job_log().read_text().splitlines()
        ]
        skipped = [e["stage"] for e in log_entries if e["event"] == "stage_skipped"]
        expected_skipped = [
            "write_script", "generate_tts", "build_timeline", "generate_lipsync",
            "prepare_background", "generate_subtitles", "compose_video",
        ]
        assert skipped == expected_skipped

    def test_resume_reruns_compose_when_final_mp4_deleted(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _run_full(tmp_path)
        job_id = ctx.job.job_id

        ctx.final_mp4().unlink()
        ctx2 = resume_pipeline(job_id, StubLLM(), StubTTS(), StubLipSync())

        assert ctx2.final_mp4().exists()

        log_entries = [
            json.loads(line) for line in ctx2.job_log().read_text().splitlines()
        ]
        events_by_stage = {e["stage"]: e["event"] for e in log_entries}
        assert events_by_stage.get("compose_video") == "stage_completed"

    def test_resume_emits_stage_skipped_for_intact_stages(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _run_full(tmp_path)
        job_id = ctx.job.job_id

        ctx.final_mp4().unlink()
        ctx2 = resume_pipeline(job_id, StubLLM(), StubTTS(), StubLipSync())

        log_entries = [
            json.loads(line) for line in ctx2.job_log().read_text().splitlines()
        ]
        skipped = {e["stage"] for e in log_entries if e["event"] == "stage_skipped"}
        for stage in ("write_script", "generate_tts", "build_timeline",
                      "generate_lipsync", "prepare_background", "generate_subtitles"):
            assert stage in skipped, f"Expected stage_skipped for '{stage}'"

    def test_resume_always_runs_finalize_job(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _run_full(tmp_path)
        job_id = ctx.job.job_id

        ctx2 = resume_pipeline(job_id, StubLLM(), StubTTS(), StubLipSync())
        log_entries = [
            json.loads(line) for line in ctx2.job_log().read_text().splitlines()
        ]
        finalize_events = [e for e in log_entries if e["stage"] == "finalize_job"]
        assert any(e["event"] == "stage_completed" for e in finalize_events)

    def test_resume_produces_final_mp4(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _run_full(tmp_path)
        job_id = ctx.job.job_id

        ctx.final_mp4().unlink()
        ctx2 = resume_pipeline(job_id, StubLLM(), StubTTS(), StubLipSync())
        assert ctx2.final_mp4().exists()


# ---------------------------------------------------------------------------
# Tests: resume_pipeline error conditions
# ---------------------------------------------------------------------------

class TestResumePipelineErrors:
    def test_resume_missing_job_input_raises_pipeline_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(PipelineError, match="job_input.json not found"):
            resume_pipeline("job_nonexistent_000", StubLLM(), StubTTS(), StubLipSync())

    def test_resume_invalid_job_input_raises_pipeline_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        # Create a workspace with a malformed job_input.json
        job_dir = tmp_path / "output" / "jobs" / "job_bad_000"
        job_dir.mkdir(parents=True, exist_ok=True)
        (job_dir / "job_input.json").write_text('{"invalid": "schema"}')
        with pytest.raises(PipelineError, match="resume"):
            resume_pipeline("job_bad_000", StubLLM(), StubTTS(), StubLipSync())
