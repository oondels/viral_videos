"""Timeline builder — concatenates audio segments and creates timeline.json."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.adapters.ffmpeg_adapter import FFmpegError, concat_audio, normalize_audio
from app.core.job_context import JobContext
from app.utils.ffprobe_utils import get_audio_duration

# Tolerance raised to 0.10s to accommodate FFmpeg resampling padding
# (22050 Hz → 44100 Hz conversion in normalize_audio may add up to ~50 ms).
_DURATION_TOLERANCE_SEC = 0.10


class TimelineError(Exception):
    """Raised when timeline building fails."""


def build_timeline(ctx: JobContext) -> list[dict[str, Any]]:
    """Build master_audio.wav and timeline.json from manifest.

    Reads audio/manifest.json, concatenates MP3 segments into master_audio.wav,
    computes start_sec/end_sec/duration_sec for each line, and writes
    timeline.json with clip_file initialized to null.

    Args:
        ctx: JobContext for canonical path resolution.

    Returns:
        The timeline as a list of dicts (matches timeline.json on disk).

    Raises:
        TimelineError: if manifest is empty, a segment file is missing,
                       FFmpeg fails, or master duration mismatches.
    """
    manifest: list[dict[str, Any]] = json.loads(
        ctx.audio_manifest().read_text(encoding="utf-8")
    )

    if not manifest:
        raise TimelineError("Manifest is empty")

    for item in manifest:
        seg_path = Path(item["audio_file"])
        if not seg_path.exists():
            raise TimelineError(f"Segment file missing: {seg_path}")

    master_path = ctx.master_audio()
    segment_paths = [Path(item["audio_file"]) for item in manifest]

    try:
        concat_audio(segment_paths, master_path)
    except FFmpegError as exc:
        raise TimelineError(f"Audio concatenation failed: {exc}") from exc

    try:
        normalize_audio(master_path, master_path)
    except FFmpegError as exc:
        raise TimelineError(f"Audio normalization failed: {exc}") from exc

    if not master_path.exists():
        raise TimelineError(f"FFmpeg did not write master audio: {master_path}")

    # Read duration AFTER normalize_audio so the measured value reflects the
    # resampled (44100 Hz stereo) master file, not the raw concatenated output.
    master_duration = get_audio_duration(master_path)

    timeline: list[dict[str, Any]] = []
    cursor = 0.0
    for item in manifest:
        dur = item["duration_sec"]
        start = round(cursor, 6)
        end = round(cursor + dur, 6)
        timeline.append(
            {
                "index": item["index"],
                "speaker": item["speaker"],
                "text": item["text"],
                "start_sec": start,
                "end_sec": end,
                "duration_sec": round(end - start, 6),
                "audio_file": item["audio_file"],
                "clip_file": None,
            }
        )
        cursor = end

    final_end = timeline[-1]["end_sec"]
    if abs(final_end - master_duration) > _DURATION_TOLERANCE_SEC:
        raise TimelineError(
            f"Timeline end ({final_end:.4f}s) does not match master audio "
            f"duration ({master_duration:.4f}s), delta "
            f"{abs(final_end - master_duration):.4f}s > {_DURATION_TOLERANCE_SEC}s"
        )

    ctx.timeline_json().parent.mkdir(parents=True, exist_ok=True)
    ctx.timeline_json().write_text(
        json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return timeline
