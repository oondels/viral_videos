"""Lip-sync engine adapter — abstract boundary for talking-head clip generation."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class LipSyncError(Exception):
    """Raised when a lip-sync engine call fails."""


class LipSyncEngine(ABC):
    """Abstract boundary for a lip-sync engine.

    Implementations are responsible for generating a talking-head video clip
    from a static character image and a per-line audio segment.

    The generated clip must:
    - be a valid MP4 file at the requested output path;
    - have duration within 0.10s of the source audio duration;
    - not include burned subtitles or title text;
    - not embed an authoritative audio track (the compositor uses master audio).
    """

    @abstractmethod
    def generate(
        self,
        image_path: Path,
        audio_path: Path,
        output_path: Path,
    ) -> Path:
        """Generate one talking-head clip.

        Args:
            image_path: Path to the character base.png asset.
            audio_path: Path to the per-line audio segment WAV file.
            output_path: Destination path for the generated MP4 clip.

        Returns:
            The output_path after the clip has been written to disk.

        Raises:
            LipSyncError: if the engine fails or the output file is not produced.
        """
