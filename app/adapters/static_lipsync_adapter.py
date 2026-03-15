"""Static image lip-sync adapter — renders character as a still image over audio.

No actual lip-sync. Useful for testing the full pipeline without a GPU or external API.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from app.adapters.lipsync_engine_adapter import LipSyncEngine, LipSyncError


class StaticImageLipSync(LipSyncEngine):
    """Renders the character base.png as a static video matching the audio duration.

    Uses FFmpeg's -loop 1 + -shortest to produce a valid MP4 without any
    external dependency. The compositor ignores the embedded audio track and
    uses master_audio.wav as the authoritative source.
    """

    def generate(self, image_path: Path, audio_path: Path, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-loop", "1", "-i", str(image_path),
                "-i", str(audio_path),
                "-c:v", "libx264", "-tune", "stillimage",
                "-c:a", "aac", "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-shortest",
                str(output_path),
            ],
            capture_output=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise LipSyncError(
                f"ffmpeg static render failed:\n{result.stderr.decode()[-300:]}"
            )
        if not output_path.exists():
            raise LipSyncError(f"ffmpeg produced no output at {output_path}")
        return output_path
