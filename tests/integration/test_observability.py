"""Integration tests for T-020: canonical stage logging and execution metadata."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from app.adapters.lipsync_engine_adapter import LipSyncEngine, LipSyncError
from app.adapters.llm_adapter import ScriptGenerator
from app.adapters.tts_provider_adapter import TTSProvider
from app.pipeline import PipelineError, run_pipeline
from app.utils.audio_utils import write_silence_wav
from app.utils.video_utils import make_color_video


# ---------------------------------------------------------------------------
# Canonical constants from spec
# ---------------------------------------------------------------------------

_CANONICAL_STAGES = {
    "validate_input",
    "init_job_workspace",
    "write_script",
    "generate_tts",
    "build_timeline",
    "generate_lipsync",
    "prepare_background",
    "generate_subtitles",
    "compose_video",
    "finalize_job",
}

_CANONICAL_EVENTS = {"stage_started", "stage_completed", "stage_failed"}

_REQUIRED_LOG_FIELDS = {"timestamp_utc", "job_id", "stage", "event", "message"}

# Stages that produce log entries (init_job_workspace through finalize_job)
_LOGGED_STAGES_IN_ORDER = [
    "init_job_workspace",
    "write_script",
    "generate_tts",
    "build_timeline",
    "generate_lipsync",
    "prepare_background",
    "generate_subtitles",
    "compose_video",
    "finalize_job",
]


# ---------------------------------------------------------------------------
# Stub providers (same pattern as test_pipeline.py)
# ---------------------------------------------------------------------------

class StubLLM(ScriptGenerator):
    def generate(self, system_prompt: str, user_prompt: str, job: Any) -> dict[str, Any]:
        chars = getattr(job, "characters", ["char_a", "char_b"])
        return {
            "title_hook": "Observability test!",
            "dialogue": [
                {"index": i + 1, "speaker": chars[i % 2], "text": f"Line {i + 1}."}
                for i in range(6)
            ],
        }


class StubTTS(TTSProvider):
    def synthesize(self, text: str, voice_id: str, output_path: Path) -> None:
        write_silence_wav(output_path, duration_sec=0.4)


class StubLipSync(LipSyncEngine):
    def generate(self, image_path: Path, audio_path: Path, output_path: Path) -> Path:
        from app.utils.ffprobe_utils import get_media_duration
        dur = get_media_duration(audio_path)
        make_color_video(output_path, duration_sec=dur, width=400, height=600)
        return output_path


class FailingLipSync(LipSyncEngine):
    def generate(self, image_path: Path, audio_path: Path, output_path: Path) -> Path:
        raise LipSyncError("observability test failure")


# ---------------------------------------------------------------------------
# Fixture helpers (identical setup as test_pipeline.py)
# ---------------------------------------------------------------------------

def _setup_assets(tmp_path: Path) -> None:
    import struct, zlib

    def _png(path: Path) -> None:
        def _c(name: bytes, data: bytes) -> bytes:
            c = struct.pack(">I", len(data)) + name + data
            return c + struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)
        path.write_bytes(
            b"\x89PNG\r\n\x1a\n"
            + _c(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
            + _c(b"IDAT", zlib.compress(b"\x00\x00\x00\x00"))
            + _c(b"IEND", b"")
        )

    for char_id in ("char_a", "char_b"):
        d = tmp_path / "assets" / "characters" / char_id
        d.mkdir(parents=True, exist_ok=True)
        _png(d / "base.png")
        (d / "metadata.json").write_text(
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
        "name": "shorts_default", "width": 1080, "height": 1920, "fps": 30,
        "title_box": {"x": 0, "y": 80, "w": 1080, "h": 140},
        "title_timing": {"start_sec": 0.0, "end_sec": 1.0},
        "title_style": {"font": "LiberationSans-Bold.ttf", "font_size": 48,
                        "color": "white", "stroke_color": "black", "stroke_width": 2, "align": "center"},
        "active_speaker_box": {"x": 40, "y": 300, "w": 400, "h": 600},
        "inactive_speaker_box": {"x": 640, "y": 380, "w": 400, "h": 600},
        "subtitle_safe_area": {"x": 40, "y": 1580, "w": 1000, "h": 280},
        "subtitle_style": {"font": "LiberationSans-Bold.ttf", "font_size": 48,
                           "color": "white", "stroke_color": "black", "stroke_width": 3, "align": "center"},
    }
    (preset_dir / "shorts_default.json").write_text(json.dumps(preset))

    bg_dir = tmp_path / "assets" / "backgrounds" / "misc"
    bg_dir.mkdir(parents=True, exist_ok=True)
    make_color_video(bg_dir / "bg.mp4", duration_sec=5.0, width=640, height=480)


def _setup_voices(tmp_path: Path) -> None:
    d = tmp_path / "config"
    d.mkdir(parents=True, exist_ok=True)
    (d / "voices.json").write_text(json.dumps({"char_a": "v_a", "char_b": "v_b"}))


def _write_job(tmp_path: Path) -> Path:
    job = {
        "topic": "observability test topic",
        "background_style": "auto",
        "characters": ["char_a", "char_b"],
        "output_preset": "shorts_default",
    }
    p = tmp_path / "job.json"
    p.write_text(json.dumps(job))
    return p


def _read_log(ctx) -> list[dict[str, Any]]:
    return [json.loads(line) for line in ctx.job_log().read_text().splitlines()]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestLogStructure:
    def test_every_log_line_is_valid_json(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _setup_voices(tmp_path)
        ctx = run_pipeline(_write_job(tmp_path), StubLLM(), StubTTS(), StubLipSync())
        for line in ctx.job_log().read_text().splitlines():
            json.loads(line)  # must not raise

    def test_every_log_entry_has_required_fields(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _setup_voices(tmp_path)
        ctx = run_pipeline(_write_job(tmp_path), StubLLM(), StubTTS(), StubLipSync())
        for entry in _read_log(ctx):
            assert _REQUIRED_LOG_FIELDS.issubset(entry.keys()), (
                f"Missing fields in log entry: {entry}"
            )

    def test_all_stage_names_are_canonical(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _setup_voices(tmp_path)
        ctx = run_pipeline(_write_job(tmp_path), StubLLM(), StubTTS(), StubLipSync())
        for entry in _read_log(ctx):
            assert entry["stage"] in _CANONICAL_STAGES, (
                f"Non-canonical stage name: {entry['stage']}"
            )

    def test_all_event_names_are_canonical(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _setup_voices(tmp_path)
        ctx = run_pipeline(_write_job(tmp_path), StubLLM(), StubTTS(), StubLipSync())
        for entry in _read_log(ctx):
            assert entry["event"] in _CANONICAL_EVENTS, (
                f"Non-canonical event: {entry['event']}"
            )

    def test_job_id_consistent_across_all_entries(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _setup_voices(tmp_path)
        ctx = run_pipeline(_write_job(tmp_path), StubLLM(), StubTTS(), StubLipSync())
        entries = _read_log(ctx)
        job_ids = {e["job_id"] for e in entries}
        assert len(job_ids) == 1
        assert ctx.job.job_id in job_ids


class TestSuccessfulRun:
    def test_each_stage_has_started_and_completed(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _setup_voices(tmp_path)
        ctx = run_pipeline(_write_job(tmp_path), StubLLM(), StubTTS(), StubLipSync())
        entries = _read_log(ctx)
        for stage in _LOGGED_STAGES_IN_ORDER:
            started = [e for e in entries if e["stage"] == stage and e["event"] == "stage_started"]
            completed = [e for e in entries if e["stage"] == stage and e["event"] == "stage_completed"]
            assert len(started) == 1, f"{stage}: expected 1 stage_started, got {len(started)}"
            assert len(completed) == 1, f"{stage}: expected 1 stage_completed, got {len(completed)}"

    def test_no_stage_failed_events_on_success(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _setup_voices(tmp_path)
        ctx = run_pipeline(_write_job(tmp_path), StubLLM(), StubTTS(), StubLipSync())
        failed = [e for e in _read_log(ctx) if e["event"] == "stage_failed"]
        assert failed == []

    def test_render_metadata_exists_after_success(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _setup_voices(tmp_path)
        ctx = run_pipeline(_write_job(tmp_path), StubLLM(), StubTTS(), StubLipSync())
        assert ctx.render_metadata().exists()


class TestFailedRun:
    def test_exactly_one_stage_failed_event_on_failure(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _setup_voices(tmp_path)
        with pytest.raises(PipelineError):
            run_pipeline(_write_job(tmp_path), StubLLM(), StubTTS(), FailingLipSync())
        # Find the job log
        jobs_dir = tmp_path / "output" / "jobs"
        ctx_dirs = list(jobs_dir.iterdir())
        assert len(ctx_dirs) == 1
        log_file = ctx_dirs[0] / "logs" / "job.log"
        entries = [json.loads(l) for l in log_file.read_text().splitlines()]
        failed = [e for e in entries if e["event"] == "stage_failed"]
        assert len(failed) == 1
        assert failed[0]["stage"] == "generate_lipsync"

    def test_failed_event_has_error_fields(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _setup_voices(tmp_path)
        with pytest.raises(PipelineError):
            run_pipeline(_write_job(tmp_path), StubLLM(), StubTTS(), FailingLipSync())
        jobs_dir = tmp_path / "output" / "jobs"
        log_file = list(jobs_dir.iterdir())[0] / "logs" / "job.log"
        entries = [json.loads(l) for l in log_file.read_text().splitlines()]
        failed = [e for e in entries if e["event"] == "stage_failed"][0]
        assert "error_type" in failed
        assert "error_message" in failed

    def test_render_metadata_absent_after_failed_render(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _setup_voices(tmp_path)
        with pytest.raises(PipelineError):
            run_pipeline(_write_job(tmp_path), StubLLM(), StubTTS(), FailingLipSync())
        jobs_dir = tmp_path / "output" / "jobs"
        render_meta = list(jobs_dir.iterdir())[0] / "render" / "render_metadata.json"
        assert not render_meta.exists()

    def test_validation_failure_produces_no_job_log(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _setup_voices(tmp_path)
        bad_job = tmp_path / "bad.json"
        bad_job.write_text(json.dumps({"topic": ""}))
        with pytest.raises(PipelineError):
            run_pipeline(bad_job, StubLLM(), StubTTS(), StubLipSync())
        assert not (tmp_path / "output" / "jobs").exists()
