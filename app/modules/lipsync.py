"""Lip-sync module — generates per-line talking-head clips and updates timeline."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.adapters.lipsync_engine_adapter import LipSyncEngine, LipSyncError
from app.core.job_context import JobContext
from app.services.asset_service import AssetError, load_character
from app.utils.ffprobe_utils import get_audio_duration

_CLIP_DURATION_TOLERANCE_SEC = 0.10


def generate_lipsync(
    ctx: JobContext,
    engine: LipSyncEngine,
) -> list[dict[str, Any]]:
    """Generate one talking-head clip per timeline item and update timeline.json.

    For each timeline item, loads the matching character asset, calls the
    engine to produce a clip, validates the clip duration, and writes the
    clip path into the timeline item's ``clip_file`` field.  No other
    timeline fields are modified.

    Args:
        ctx: JobContext for canonical path resolution.
        engine: LipSyncEngine implementation.

    Returns:
        The updated timeline as a list of dicts (matches timeline.json on disk).

    Raises:
        AssetError: if the character asset for any speaker is missing.
        LipSyncError: if the engine fails or the clip is not written.
        RuntimeError: if the generated clip duration is outside the tolerance.
    """
    timeline: list[dict[str, Any]] = json.loads(
        ctx.timeline_json().read_text(encoding="utf-8")
    )

    ctx.clips_dir().mkdir(parents=True, exist_ok=True)

    for item in timeline:
        speaker: str = item["speaker"]
        index: int = item["index"]
        audio_path = Path(item["audio_file"])

        if not audio_path.exists():
            raise LipSyncError(
                f"Source audio file missing for item {index}: {audio_path}"
            )

        char_assets = load_character(speaker)
        image_path: Path = char_assets["base_png"]

        clip_path = ctx.clip(index, speaker)

        engine.generate(image_path, audio_path, clip_path)

        if not clip_path.exists():
            raise LipSyncError(
                f"Engine did not produce clip for item {index}: {clip_path}"
            )

        audio_duration = item["duration_sec"]
        clip_duration = get_audio_duration(clip_path)
        if abs(clip_duration - audio_duration) > _CLIP_DURATION_TOLERANCE_SEC:
            raise RuntimeError(
                f"Clip duration ({clip_duration:.4f}s) for item {index} exceeds "
                f"tolerance versus audio ({audio_duration:.4f}s): "
                f"delta {abs(clip_duration - audio_duration):.4f}s "
                f"> {_CLIP_DURATION_TOLERANCE_SEC}s"
            )

        item["clip_file"] = str(clip_path)

    ctx.timeline_json().write_text(
        json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return timeline
