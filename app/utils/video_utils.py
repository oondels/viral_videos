"""Video utilities — convenience wrappers for common video operations."""
from __future__ import annotations

import subprocess
from pathlib import Path

from app.utils.ffprobe_utils import get_media_duration, get_video_dimensions

_FFMPEG_TIMEOUT_SEC = 30


def make_color_video(
    path: Path,
    duration_sec: float,
    width: int = 640,
    height: int = 480,
    color: str = "black",
    fps: int = 30,
) -> None:
    """Generate a solid-color video using FFmpeg lavfi.

    Useful for creating test fixtures and placeholder clips without real footage.

    Args:
        path: Destination file path.
        duration_sec: Video duration in seconds.
        width: Frame width in pixels.
        height: Frame height in pixels.
        color: FFmpeg color name or hex value.
        fps: Frame rate.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c={color}:s={width}x{height}:r={fps}:d={duration_sec}",
            "-c:v", "libx264",
            "-t", str(duration_sec),
            str(path),
        ],
        capture_output=True,
        timeout=_FFMPEG_TIMEOUT_SEC,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to create color video {path}: "
            f"{result.stderr.decode(errors='replace').strip()}"
        )


__all__ = ["get_media_duration", "get_video_dimensions", "make_color_video"]
