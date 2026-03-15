from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.contracts import ValidatedJob
from app.utils.path_utils import job_root


@dataclass(frozen=True)
class JobContext:
    """Central path authority for a single job workspace.

    All artifact path resolution goes through this class.
    Modules must not assemble canonical paths by hand.
    """

    job: ValidatedJob

    # ------------------------------------------------------------------ #
    # Root                                                                 #
    # ------------------------------------------------------------------ #

    def root(self) -> Path:
        return job_root(self.job.job_id)

    # ------------------------------------------------------------------ #
    # Script                                                               #
    # ------------------------------------------------------------------ #

    def script_dir(self) -> Path:
        return self.root() / "script"

    def script_json(self) -> Path:
        return self.script_dir() / "script.json"

    def dialogue_json(self) -> Path:
        return self.script_dir() / "dialogue.json"

    def timeline_json(self) -> Path:
        return self.script_dir() / "timeline.json"

    # ------------------------------------------------------------------ #
    # Audio                                                                #
    # ------------------------------------------------------------------ #

    def audio_dir(self) -> Path:
        return self.root() / "audio"

    def audio_segments_dir(self) -> Path:
        return self.audio_dir() / "segments"

    def audio_segment(self, index: int, character: str) -> Path:
        """Return the canonical path for one audio segment file."""
        return self.audio_segments_dir() / f"{index:03d}_{character}.wav"

    def audio_manifest(self) -> Path:
        return self.audio_dir() / "manifest.json"

    def audio_master_dir(self) -> Path:
        return self.audio_dir() / "master"

    def master_audio(self) -> Path:
        return self.audio_master_dir() / "master_audio.wav"

    # ------------------------------------------------------------------ #
    # Clips                                                                #
    # ------------------------------------------------------------------ #

    def clips_dir(self) -> Path:
        return self.root() / "clips"

    def clip(self, index: int, character: str) -> Path:
        """Return the canonical path for one talking-head clip."""
        return self.clips_dir() / f"{index:03d}_{character}_talk.mp4"

    # ------------------------------------------------------------------ #
    # Background                                                           #
    # ------------------------------------------------------------------ #

    def background_dir(self) -> Path:
        return self.root() / "background"

    def prepared_background(self) -> Path:
        return self.background_dir() / "prepared_background.mp4"

    # ------------------------------------------------------------------ #
    # Subtitles                                                            #
    # ------------------------------------------------------------------ #

    def subtitles_dir(self) -> Path:
        return self.root() / "subtitles"

    def subtitles_srt(self) -> Path:
        return self.subtitles_dir() / "subtitles.srt"

    # ------------------------------------------------------------------ #
    # Render                                                               #
    # ------------------------------------------------------------------ #

    def render_dir(self) -> Path:
        return self.root() / "render"

    def final_mp4(self) -> Path:
        return self.render_dir() / "final.mp4"

    def render_metadata(self) -> Path:
        return self.render_dir() / "render_metadata.json"

    # ------------------------------------------------------------------ #
    # Logs                                                                 #
    # ------------------------------------------------------------------ #

    def logs_dir(self) -> Path:
        return self.root() / "logs"

    def job_log(self) -> Path:
        return self.logs_dir() / "job.log"
