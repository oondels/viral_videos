"""Static image lip-sync adapter — renders character as a still image over audio.

No actual lip-sync. Useful for testing the full pipeline without a GPU or external API.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from app.adapters.lipsync_engine_adapter import LipSyncEngine, LipSyncError
from app.utils.ffprobe_utils import get_audio_duration


class StaticImageLipSync(LipSyncEngine):
    """Renders the character base.png as a static video matching the audio duration.

    Uses FFmpeg's -loop 1 with an explicit -t duration to produce a video-only
    MP4 (no embedded audio track).  The compositor uses master_audio.wav as the
    authoritative audio source.
    """

    def generate(self, image_path: Path, audio_path: Path, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        duration = get_audio_duration(audio_path)
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-loop", "1", "-i", str(image_path),
                "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p",
                "-c:v", "libx264", "-tune", "stillimage",
                "-pix_fmt", "yuv420p",
                "-t", str(duration),
                "-an",
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
