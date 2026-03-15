"""Render service — writes render_metadata.json for a completed job."""
from __future__ import annotations

import json
from typing import Any

from app.core.job_context import JobContext
from app.utils.ffprobe_utils import get_media_duration


_REQUIRED_METADATA_FIELDS = {
    "job_id",
    "output_file",
    "duration_sec",
    "preset_name",
    "background_file",
    "subtitle_file",
    "timeline_item_count",
}


def write_render_metadata(
    ctx: JobContext,
    preset_name: str,
    timeline_item_count: int,
) -> dict[str, Any]:
    """Measure the final video and write render_metadata.json.

    Args:
        ctx: JobContext for canonical path resolution.
        preset_name: Name of the render preset used.
        timeline_item_count: Number of timeline items composed.

    Returns:
        The metadata dict (also written to disk).

    Raises:
        RuntimeError: if the final MP4 does not exist or cannot be probed.
    """
    final = ctx.final_mp4()
    if not final.exists():
        raise RuntimeError(f"Final MP4 not found: {final}")

    duration = get_media_duration(final)

    metadata: dict[str, Any] = {
        "job_id": ctx.job.job_id,
        "output_file": str(final),
        "duration_sec": round(duration, 4),
        "preset_name": preset_name,
        "background_file": str(ctx.prepared_background()),
        "subtitle_file": str(ctx.subtitles_srt()),
        "timeline_item_count": timeline_item_count,
    }

    ctx.render_dir().mkdir(parents=True, exist_ok=True)
    ctx.render_metadata().write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return metadata
