"""Background selector — selects, loops/trims, and normalises the background video."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from app.core.job_context import JobContext
from app.services.asset_service import AssetError, list_backgrounds
from app.utils.ffprobe_utils import get_audio_duration

_FFMPEG_TIMEOUT_SEC = 120
_TARGET_WIDTH = 1080
_TARGET_HEIGHT = 1920
_ALL_CATEGORIES = ("slime", "sand", "minecraft_parkour", "marble_run", "misc")


class BackgroundError(Exception):
    """Raised when background selection or preparation fails."""


def _get_video_duration(path: Path) -> float:
    """Return duration of a video file in seconds using ffprobe."""
    return get_audio_duration(path)


def _select_background(style: str, job_id: str) -> Path:
    """Select exactly one background file for the given style.

    Args:
        style: 'auto' or a named category.
        job_id: used for deterministic auto-selection.

    Returns:
        Path to the selected background file.

    Raises:
        BackgroundError: if no background file is found.
    """
    if style == "auto":
        candidates: list[Path] = []
        for cat in _ALL_CATEGORIES:
            try:
                candidates.extend(list_backgrounds(cat))
            except AssetError:
                pass
        if not candidates:
            raise BackgroundError(
                "No background assets found in any category for 'auto' selection"
            )
        # Deterministic pick: stable hash of job_id mod number of candidates
        digest = int(hashlib.md5(job_id.encode()).hexdigest(), 16)
        return candidates[digest % len(candidates)]

    files = list_backgrounds(style)
    if not files:
        raise BackgroundError(
            f"No background assets found in category '{style}'"
        )
    digest = int(hashlib.md5(job_id.encode()).hexdigest(), 16)
    return files[digest % len(files)]


def prepare_background(ctx: JobContext, required_duration_sec: float) -> Path:
    """Select one background asset and produce prepared_background.mp4.

    Selects the background based on the job's background_style, then loops
    or trims the source to at least required_duration_sec and scales to
    1080x1920 (scale-to-cover + crop).  No audio track is included.

    Args:
        ctx: JobContext for canonical path resolution.
        required_duration_sec: minimum duration the prepared background must cover.

    Returns:
        Path to the prepared background file.

    Raises:
        BackgroundError: if selection fails, FFmpeg fails, or the output
                         duration is shorter than required.
    """
    style = ctx.job.background_style
    job_id = ctx.job.job_id

    source = _select_background(style, job_id)

    try:
        source_duration = _get_video_duration(source)
    except Exception as exc:
        raise BackgroundError(
            f"Cannot read background file {source}: {exc}"
        ) from exc

    ctx.background_dir().mkdir(parents=True, exist_ok=True)
    output = ctx.prepared_background()

    # Build FFmpeg command: loop if needed, scale-to-cover, crop, trim, no audio
    need_loop = source_duration < required_duration_sec
    scale_filter = (
        f"scale={_TARGET_WIDTH}:{_TARGET_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={_TARGET_WIDTH}:{_TARGET_HEIGHT}"
    )

    cmd = ["ffmpeg", "-y"]
    if need_loop:
        cmd += ["-stream_loop", "-1"]
    cmd += ["-i", str(source)]
    cmd += [
        "-vf", scale_filter,
        "-t", str(required_duration_sec),
        "-an",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        str(output),
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=_FFMPEG_TIMEOUT_SEC,
    )
    if result.returncode != 0:
        raise BackgroundError(
            f"FFmpeg failed preparing background (exit {result.returncode}): "
            f"{result.stderr.strip()}"
        )

    if not output.exists():
        raise BackgroundError(f"FFmpeg did not produce prepared background: {output}")

    actual_duration = _get_video_duration(output)
    # Allow 1 frame tolerance (at 30fps)
    tolerance = 1.0 / 30.0
    if actual_duration < required_duration_sec - tolerance:
        raise BackgroundError(
            f"Prepared background duration ({actual_duration:.4f}s) is shorter "
            f"than required ({required_duration_sec:.4f}s)"
        )

    return output
