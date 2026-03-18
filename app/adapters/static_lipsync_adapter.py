"""Static image lip-sync adapter — renders character as alpha-preserving video.

No actual lip-sync.  The character is static, so the adapter encodes the PNG
into a QuickTime RLE video (ARGB pixel format) which preserves the alpha
channel.  The compositor's ``format=rgba`` filter then uses the alpha for
correct overlay blending.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from app.adapters.lipsync_engine_adapter import LipSyncEngine, LipSyncError
from app.utils.ffprobe_utils import get_audio_duration


class StaticImageLipSync(LipSyncEngine):
    """Encodes the character base.png as a still video with alpha channel.

    Uses FFmpeg ``qtrle`` codec with ``argb`` pixel format inside a MOV
    container (written to the .mp4 output path).  This preserves the PNG
    alpha channel that ``libx264`` / ``yuv420p`` would discard.
    """

    def generate(self, image_path: Path, audio_path: Path, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        duration = get_audio_duration(audio_path)
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-loop", "1", "-i", str(image_path),
                "-c:v", "qtrle",
                "-pix_fmt", "argb",
                "-t", str(duration),
                "-an",
                "-f", "mov",
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
