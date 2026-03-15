"""FFprobe utilities for measuring media file properties."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

_FFPROBE_TIMEOUT_SEC = 10


def _run_ffprobe(args: list[str]) -> dict[str, Any]:
    """Run ffprobe with the given args and return parsed JSON output."""
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=_FFPROBE_TIMEOUT_SEC,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"ffprobe failed (exit {result.returncode}): {result.stderr.strip()}"
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Could not parse ffprobe output: {exc}") from exc


def get_media_duration(path: Path) -> float:
    """Return the duration in seconds of any media file using ffprobe.

    Args:
        path: Path to the audio or video file.

    Returns:
        Duration in seconds (float, > 0).

    Raises:
        RuntimeError: if ffprobe fails or the file is unreadable.
        ValueError: if the measured duration is zero or negative.
    """
    data = _run_ffprobe([
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_entries", "format=duration",
        str(path),
    ])
    try:
        duration = float(data["format"]["duration"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError(
            f"Could not parse duration from ffprobe output for {path}: {exc}"
        ) from exc
    if duration <= 0:
        raise ValueError(f"File {path} has zero or negative duration: {duration}")
    return duration


def get_video_dimensions(path: Path) -> tuple[int, int]:
    """Return the (width, height) of the first video stream in a file.

    Args:
        path: Path to the video file.

    Returns:
        Tuple of (width, height) in pixels.

    Raises:
        RuntimeError: if ffprobe fails or no video stream is found.
    """
    data = _run_ffprobe([
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_entries", "stream=width,height,codec_type",
        str(path),
    ])
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            try:
                return int(stream["width"]), int(stream["height"])
            except (KeyError, TypeError, ValueError) as exc:
                raise RuntimeError(
                    f"Could not read dimensions from stream: {exc}"
                ) from exc
    raise RuntimeError(f"No video stream found in {path}")


def get_audio_duration(path: Path) -> float:
    """Return the duration in seconds of an audio file using ffprobe.

    Delegates to get_media_duration; kept for backward compatibility.

    Args:
        path: Path to the audio file.

    Returns:
        Duration in seconds (float, > 0).

    Raises:
        RuntimeError: if ffprobe fails or the file is unreadable.
        ValueError: if the measured duration is zero or negative.
    """
    return get_media_duration(path)
