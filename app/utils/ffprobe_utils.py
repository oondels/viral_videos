"""FFprobe utilities for measuring media file properties."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

_FFPROBE_TIMEOUT_SEC = 10


def get_audio_duration(path: Path) -> float:
    """Return the duration in seconds of an audio file using ffprobe.

    Args:
        path: Path to the audio file.

    Returns:
        Duration in seconds (float, > 0).

    Raises:
        RuntimeError: if ffprobe fails or the file is unreadable.
        ValueError: if the measured duration is zero or negative.
    """
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_entries", "format=duration",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=_FFPROBE_TIMEOUT_SEC,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"ffprobe failed for {path} (exit {result.returncode}): {result.stderr.strip()}"
        )
    try:
        data = json.loads(result.stdout)
        duration = float(data["format"]["duration"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise RuntimeError(
            f"Could not parse ffprobe output for {path}: {exc}"
        ) from exc

    if duration <= 0:
        raise ValueError(
            f"Audio file {path} has zero or negative duration: {duration}"
        )
    return duration
