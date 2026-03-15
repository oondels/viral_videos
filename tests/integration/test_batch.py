"""Integration tests for T-021: sequential batch processing and report."""
from __future__ import annotations

import json
import shutil
import struct
import zlib
from pathlib import Path
from typing import Any

import pytest

from app.adapters.lipsync_engine_adapter import LipSyncEngine, LipSyncError
from app.adapters.llm_adapter import ScriptGenerator, ScriptGenerationError
from app.adapters.tts_provider_adapter import TTSProvider
from app.batch import run_batch
from app.utils.audio_utils import write_silence_wav
from app.utils.video_utils import make_color_video


# ---------------------------------------------------------------------------
# Stub providers (same pattern as test_pipeline.py)
# ---------------------------------------------------------------------------

class StubLLM(ScriptGenerator):
    def generate(self, system_prompt: str, user_prompt: str, job: Any) -> dict[str, Any]:
        chars = list(job.characters)
        lines = [
            {"index": 1, "speaker": chars[0], "text": "Hello!"},
            {"index": 2, "speaker": chars[1], "text": "Hi there!"},
            {"index": 3, "speaker": chars[0], "text": "How are you?"},
            {"index": 4, "speaker": chars[1], "text": "Great, thanks!"},
            {"index": 5, "speaker": chars[0], "text": "Doing well."},
            {"index": 6, "speaker": chars[1], "text": "Glad to hear!"},
        ]
        return {"title_hook": "Batch Test Hook!", "dialogue": lines}


class StubTTS(TTSProvider):
    def synthesize(self, text: str, voice_id: str, output_path: Path) -> None:
        write_silence_wav(output_path, duration_sec=0.3)


class StubLipSync(LipSyncEngine):
    def generate(self, image_path: Path, audio_path: Path, output_path: Path) -> Path:
        from app.utils.ffprobe_utils import get_media_duration
        dur = get_media_duration(audio_path)
        make_color_video(output_path, duration_sec=dur, width=400, height=600)
        return output_path


class FailingLipSync(LipSyncEngine):
    def generate(self, image_path: Path, audio_path: Path, output_path: Path) -> Path:
        raise LipSyncError("stub failure")


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _png_bytes() -> bytes:
    def _chunk(name: bytes, data: bytes) -> bytes:
        c = struct.pack(">I", len(data)) + name + data
        return c + struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00"))
        + _chunk(b"IEND", b"")
    )


def _setup_assets(tmp_path: Path) -> None:
    for char_id in ("char_a", "char_b"):
        char_dir = tmp_path / "assets" / "characters" / char_id
        char_dir.mkdir(parents=True, exist_ok=True)
        (char_dir / "base.png").write_bytes(_png_bytes())
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


def _setup_voice_config(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "voices.json").write_text(
        json.dumps({"char_a": "v_a", "char_b": "v_b"})
    )


def _write_csv(tmp_path: Path, rows: list[str], header: bool = True) -> Path:
    csv_file = tmp_path / "jobs.csv"
    lines = []
    if header:
        lines.append("topic,duration_target_sec,background_style,characters,output_preset")
    lines.extend(rows)
    csv_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return csv_file


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestBatchAllSucceed:
    def test_two_valid_items_produce_two_workspaces(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _setup_voice_config(tmp_path)
        csv_file = _write_csv(tmp_path, [
            "Why do cats knock things off tables?,30,auto,char_a|char_b,shorts_default",
            "Explain inflation humorously,30,auto,char_a|char_b,shorts_default",
        ])
        report = run_batch(csv_file, StubLLM(), StubTTS(), StubLipSync())
        assert report["total_jobs"] == 2
        assert report["succeeded_jobs"] == 2
        assert report["failed_jobs"] == 0
        jobs_dir = tmp_path / "output" / "jobs"
        assert jobs_dir.exists()
        assert len(list(jobs_dir.iterdir())) == 2

    def test_report_written_to_canonical_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _setup_voice_config(tmp_path)
        csv_file = _write_csv(tmp_path, [
            "A fun topic,30,auto,char_a|char_b,shorts_default",
        ])
        run_batch(csv_file, StubLLM(), StubTTS(), StubLipSync())
        report_path = tmp_path / "output" / "batch_reports" / "latest_report.json"
        assert report_path.exists()
        report = json.loads(report_path.read_text())
        assert report["total_jobs"] == 1

    def test_report_contains_required_top_level_fields(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _setup_voice_config(tmp_path)
        csv_file = _write_csv(tmp_path, [
            "A fun topic,30,auto,char_a|char_b,shorts_default",
        ])
        report = run_batch(csv_file, StubLLM(), StubTTS(), StubLipSync())
        for field in ("started_at", "finished_at", "total_jobs", "succeeded_jobs", "failed_jobs", "items"):
            assert field in report, f"missing field: {field}"

    def test_each_item_has_required_fields(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _setup_voice_config(tmp_path)
        csv_file = _write_csv(tmp_path, [
            "A fun topic,30,auto,char_a|char_b,shorts_default",
        ])
        report = run_batch(csv_file, StubLLM(), StubTTS(), StubLipSync())
        item = report["items"][0]
        for field in ("job_id", "input_ref", "status", "output_file", "error_message"):
            assert field in item, f"missing field: {field}"

    def test_successful_item_has_output_file_and_no_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _setup_voice_config(tmp_path)
        csv_file = _write_csv(tmp_path, [
            "A fun topic,30,auto,char_a|char_b,shorts_default",
        ])
        report = run_batch(csv_file, StubLLM(), StubTTS(), StubLipSync())
        item = report["items"][0]
        assert item["status"] == "success"
        assert item["output_file"] is not None
        assert item["error_message"] is None
        assert item["job_id"] is not None


class TestBatchMixedResults:
    def test_invalid_row_does_not_stop_subsequent_items(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _setup_voice_config(tmp_path)
        # Row 1: invalid (no topic), Row 2: valid
        csv_file = _write_csv(tmp_path, [
            ",30,auto,char_a|char_b,shorts_default",  # empty topic
            "Valid topic,30,auto,char_a|char_b,shorts_default",
        ])
        report = run_batch(csv_file, StubLLM(), StubTTS(), StubLipSync())
        assert report["total_jobs"] == 2
        assert report["succeeded_jobs"] == 1
        assert report["failed_jobs"] == 1
        assert report["items"][0]["status"] == "failed"
        assert report["items"][1]["status"] == "success"

    def test_pipeline_failure_continues_batch(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _setup_voice_config(tmp_path)
        csv_file = _write_csv(tmp_path, [
            "Topic one,30,auto,char_a|char_b,shorts_default",
            "Topic two,30,auto,char_a|char_b,shorts_default",
        ])
        # First item will fail (lipsync), second also but batch must complete
        report = run_batch(csv_file, StubLLM(), StubTTS(), FailingLipSync())
        assert report["total_jobs"] == 2
        assert report["failed_jobs"] == 2
        assert report["succeeded_jobs"] == 0

    def test_failed_item_has_error_message_and_no_output(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _setup_voice_config(tmp_path)
        csv_file = _write_csv(tmp_path, [
            ",30,auto,char_a|char_b,shorts_default",  # empty topic → parse error
        ])
        report = run_batch(csv_file, StubLLM(), StubTTS(), StubLipSync())
        item = report["items"][0]
        assert item["status"] == "failed"
        assert item["error_message"] is not None
        assert item["output_file"] is None


class TestBatchEdgeCases:
    def test_unreadable_batch_file_raises_value_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _setup_voice_config(tmp_path)
        from app.batch import run_batch as _run_batch
        with pytest.raises(ValueError, match="Cannot read batch file"):
            _run_batch(
                tmp_path / "nonexistent.csv",
                StubLLM(), StubTTS(), StubLipSync(),
            )

    def test_each_item_gets_isolated_workspace(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_assets(tmp_path)
        _setup_voice_config(tmp_path)
        csv_file = _write_csv(tmp_path, [
            "Topic A,30,auto,char_a|char_b,shorts_default",
            "Topic B,30,auto,char_a|char_b,shorts_default",
        ])
        report = run_batch(csv_file, StubLLM(), StubTTS(), StubLipSync())
        job_ids = [it["job_id"] for it in report["items"] if it["job_id"]]
        assert len(job_ids) == 2
        assert job_ids[0] != job_ids[1]
