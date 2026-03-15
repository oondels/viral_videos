"""Timeline builder — concatenates audio segments and creates timeline.json."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from app.core.job_context import JobContext
from app.utils.ffprobe_utils import get_audio_duration

_FFMPEG_TIMEOUT_SEC = 60
_DURATION_TOLERANCE_SEC = 0.05


class TimelineError(Exception):
    """Raised when timeline building fails."""


def build_timeline(ctx: JobContext) -> list[dict[str, Any]]:
    """Build master_audio.wav and timeline.json from manifest.

    Reads audio/manifest.json, concatenates segments into master_audio.wav,
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

    ctx.audio_master_dir().mkdir(parents=True, exist_ok=True)
    master_path = ctx.master_audio()

    concat_list = ctx.audio_master_dir() / "concat_list.txt"
    list_lines = [
        f"file '{Path(item['audio_file']).resolve()}'" for item in manifest
    ]
    concat_list.write_text("\n".join(list_lines), encoding="utf-8")

    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            str(master_path),
        ],
        capture_output=True,
        text=True,
        timeout=_FFMPEG_TIMEOUT_SEC,
    )
    if result.returncode != 0:
        raise TimelineError(
            f"FFmpeg concatenation failed (exit {result.returncode}): "
            f"{result.stderr.strip()}"
        )

    if not master_path.exists():
        raise TimelineError(f"FFmpeg did not write master audio: {master_path}")

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
