"""Subtitles module — generates subtitles.srt from the canonical timeline."""
from __future__ import annotations

import json
from typing import Any

from app.core.job_context import JobContext


class SubtitleError(Exception):
    """Raised when subtitle generation fails."""


def _sec_to_srt_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format HH:MM:SS,mmm."""
    if seconds < 0:
        seconds = 0.0
    total_ms = round(seconds * 1000)
    ms = total_ms % 1000
    total_s = total_ms // 1000
    s = total_s % 60
    total_m = total_s // 60
    m = total_m % 60
    h = total_m // 60
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def generate_subtitles(ctx: JobContext) -> str:
    """Generate subtitles.srt from timeline.json.

    Produces one SRT cue per timeline item using timeline text and timing
    as the sole source of truth. Text is never rewritten or paraphrased.

    Args:
        ctx: JobContext for canonical path resolution.

    Returns:
        The SRT content string (also written to disk).

    Raises:
        SubtitleError: if the timeline is missing, unordered, or a cue
                       has end <= start.
    """
    timeline_path = ctx.timeline_json()
    if not timeline_path.exists():
        raise SubtitleError(f"Timeline file missing: {timeline_path}")

    timeline: list[dict[str, Any]] = json.loads(
        timeline_path.read_text(encoding="utf-8")
    )

    if not timeline:
        raise SubtitleError("Timeline is empty")

    # Validate ordering
    for i in range(len(timeline) - 1):
        if timeline[i]["start_sec"] >= timeline[i + 1]["start_sec"]:
            raise SubtitleError(
                f"Timeline items are unordered at index {i} → {i + 1}"
            )

    cues: list[str] = []
    for cue_num, item in enumerate(timeline, start=1):
        start = item["start_sec"]
        end = item["end_sec"]
        if end <= start:
            raise SubtitleError(
                f"Cue {cue_num}: end ({end}) <= start ({start})"
            )
        cues.append(
            f"{cue_num}\n"
            f"{_sec_to_srt_timestamp(start)} --> {_sec_to_srt_timestamp(end)}\n"
            f"{item['text']}"
        )

    srt_content = "\n\n".join(cues) + "\n"

    ctx.subtitles_dir().mkdir(parents=True, exist_ok=True)
    ctx.subtitles_srt().write_text(srt_content, encoding="utf-8")

    return srt_content
