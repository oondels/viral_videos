"""Unit tests for T-005: job context and canonical workspace path services."""

import pytest

from app.core.contracts import ValidatedJob
from app.core.job_context import JobContext
from app.services.file_service import init_workspace


def _make_job(job_id: str = "job_2026_03_15_001") -> ValidatedJob:
    return ValidatedJob(
        job_id=job_id,
        topic="test topic",
        duration_target_sec=30,
        characters=["char_a", "char_b"],
        background_style="auto",
        output_preset="shorts_default",
    )


def _make_ctx(job_id: str = "job_2026_03_15_001") -> JobContext:
    return JobContext(job=_make_job(job_id))


class TestJobContextPaths:
    def test_root_contains_job_id(self):
        ctx = _make_ctx("job_2026_03_15_042")
        assert str(ctx.root()).endswith("job_2026_03_15_042")

    def test_root_under_output_jobs(self):
        ctx = _make_ctx("job_2026_03_15_001")
        parts = ctx.root().parts
        assert "output" in parts
        assert "jobs" in parts

    def test_script_dir(self):
        ctx = _make_ctx()
        assert ctx.script_dir() == ctx.root() / "script"

    def test_script_json(self):
        ctx = _make_ctx()
        assert ctx.script_json() == ctx.script_dir() / "script.json"

    def test_dialogue_json(self):
        ctx = _make_ctx()
        assert ctx.dialogue_json() == ctx.script_dir() / "dialogue.json"

    def test_timeline_json(self):
        ctx = _make_ctx()
        assert ctx.timeline_json() == ctx.script_dir() / "timeline.json"

    def test_audio_segments_dir(self):
        ctx = _make_ctx()
        assert ctx.audio_segments_dir() == ctx.audio_dir() / "segments"

    def test_audio_segment_naming(self):
        ctx = _make_ctx()
        path = ctx.audio_segment(1, "char_a")
        assert path.name == "001_char_a.wav"

    def test_audio_segment_index_padding(self):
        ctx = _make_ctx()
        assert ctx.audio_segment(7, "char_b").name == "007_char_b.wav"

    def test_audio_manifest(self):
        ctx = _make_ctx()
        assert ctx.audio_manifest() == ctx.audio_dir() / "manifest.json"

    def test_master_audio(self):
        ctx = _make_ctx()
        assert ctx.master_audio() == ctx.audio_master_dir() / "master_audio.wav"

    def test_clip_naming(self):
        ctx = _make_ctx()
        assert ctx.clip(2, "char_b").name == "002_char_b_talk.mp4"

    def test_prepared_background(self):
        ctx = _make_ctx()
        assert ctx.prepared_background() == ctx.background_dir() / "prepared_background.mp4"

    def test_subtitles_srt(self):
        ctx = _make_ctx()
        assert ctx.subtitles_srt() == ctx.subtitles_dir() / "subtitles.srt"

    def test_final_mp4(self):
        ctx = _make_ctx()
        assert ctx.final_mp4() == ctx.render_dir() / "final.mp4"

    def test_render_metadata(self):
        ctx = _make_ctx()
        assert ctx.render_metadata() == ctx.render_dir() / "render_metadata.json"

    def test_job_log(self):
        ctx = _make_ctx()
        assert ctx.job_log() == ctx.logs_dir() / "job.log"

    def test_all_paths_under_root(self):
        ctx = _make_ctx("job_2026_03_15_099")
        root = ctx.root()
        paths = [
            ctx.script_dir(),
            ctx.dialogue_json(),
            ctx.timeline_json(),
            ctx.audio_segments_dir(),
            ctx.audio_manifest(),
            ctx.audio_master_dir(),
            ctx.clips_dir(),
            ctx.background_dir(),
            ctx.subtitles_dir(),
            ctx.render_dir(),
            ctx.logs_dir(),
        ]
        for path in paths:
            assert str(path).startswith(str(root)), f"{path} is not under {root}"


class TestInitWorkspace:
    def test_creates_all_canonical_dirs(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx("job_2026_03_15_001")
        init_workspace(ctx)

        expected = [
            ctx.script_dir(),
            ctx.audio_segments_dir(),
            ctx.audio_master_dir(),
            ctx.clips_dir(),
            ctx.background_dir(),
            ctx.subtitles_dir(),
            ctx.render_dir(),
            ctx.logs_dir(),
        ]
        for d in expected:
            assert d.is_dir(), f"Expected directory to exist: {d}"

    def test_idempotent(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx("job_2026_03_15_002")
        init_workspace(ctx)
        init_workspace(ctx)  # must not raise

    def test_no_assets_dir_created(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx("job_2026_03_15_003")
        init_workspace(ctx)
        assets_dir = tmp_path / "assets"
        assert not assets_dir.exists()

    def test_workspace_under_output_jobs(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx("job_2026_03_15_004")
        init_workspace(ctx)
        workspace = tmp_path / "output" / "jobs" / "job_2026_03_15_004"
        assert workspace.is_dir()
