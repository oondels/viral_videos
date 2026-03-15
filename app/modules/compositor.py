"""Compositor — assembles the final MP4 from all pipeline artifacts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.adapters.ffmpeg_adapter import FFmpegError, run_ffmpeg
from app.core.job_context import JobContext
from app.services.asset_service import load_character, load_preset, resolve_font
from app.services.render_service import write_render_metadata
from app.utils.ffprobe_utils import get_media_duration

_RENDER_TIMEOUT_SEC = 600
_DURATION_TOLERANCE_SEC = 0.10


class CompositorError(Exception):
    """Raised when video composition fails."""


def _escape_ffmpeg_path(path: Path) -> str:
    """Escape a path for use in FFmpeg filter arguments."""
    return str(path).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


def _escape_drawtext(text: str) -> str:
    """Escape text for use in FFmpeg drawtext filter."""
    return (
        text
        .replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace(":", "\\:")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )


def compose_video(ctx: JobContext) -> Path:
    """Compose all pipeline artifacts into the final MP4.

    Builds a single FFmpeg filter_complex that:
    - scales the prepared background to 1080x1920;
    - overlays the active speaker clip at each timeline segment;
    - overlays the inactive speaker base.png at each timeline segment;
    - burns the title hook for the first 2 seconds;
    - burns subtitles from the SRT file;
    - mixes master_audio.wav as the authoritative audio track.

    Args:
        ctx: JobContext for canonical path resolution.

    Returns:
        Path to the rendered final.mp4.

    Raises:
        CompositorError: if a required artifact is missing or FFmpeg fails.
    """
    # ------------------------------------------------------------------ #
    # Load artifacts                                                       #
    # ------------------------------------------------------------------ #
    for label, path in [
        ("prepared_background", ctx.prepared_background()),
        ("master_audio", ctx.master_audio()),
        ("timeline", ctx.timeline_json()),
        ("subtitles", ctx.subtitles_srt()),
        ("script", ctx.script_json()),
    ]:
        if not path.exists():
            raise CompositorError(f"Required artifact missing: {label} → {path}")

    timeline: list[dict[str, Any]] = json.loads(
        ctx.timeline_json().read_text(encoding="utf-8")
    )
    script: dict[str, Any] = json.loads(
        ctx.script_json().read_text(encoding="utf-8")
    )
    preset = load_preset(ctx.job.output_preset)

    # Validate clips exist
    for item in timeline:
        if not item.get("clip_file"):
            raise CompositorError(
                f"Timeline item {item['index']} has no clip_file"
            )
        if not Path(item["clip_file"]).exists():
            raise CompositorError(
                f"Clip file missing for item {item['index']}: {item['clip_file']}"
            )

    # Resolve fonts
    title_font = resolve_font(preset["title_style"]["font"])
    sub_font = resolve_font(preset["subtitle_style"]["font"])

    # Preset geometry
    W = preset["width"]
    H = preset["height"]
    abox = preset["active_speaker_box"]
    ibox = preset["inactive_speaker_box"]
    title_box = preset["title_box"]
    title_timing = preset["title_timing"]
    title_style = preset["title_style"]
    sub_style = preset["subtitle_style"]

    total_duration = timeline[-1]["end_sec"]
    all_speakers = sorted(set(item["speaker"] for item in timeline))

    # ------------------------------------------------------------------ #
    # Build FFmpeg input list                                              #
    # ------------------------------------------------------------------ #
    # Input 0: background
    # Input 1..N: clips (with -itsoffset for temporal positioning)
    # Input N+1..N+M: inactive speaker images (one per timeline item)
    # Input last: master audio

    cmd: list[str] = ["ffmpeg", "-y"]

    cmd += ["-i", str(ctx.prepared_background())]     # [0] background
    bg_idx = 0

    clip_indices: list[int] = []
    for item in timeline:
        cmd += ["-itsoffset", str(item["start_sec"]), "-i", str(item["clip_file"])]
        clip_indices.append(len(clip_indices) + 1)   # [1, 2, 3, ...]

    inactive_img_indices: list[int] = []
    for item in timeline:
        speaker = item["speaker"]
        inactive_id = [c for c in all_speakers if c != speaker][0]
        char = load_character(inactive_id)
        cmd += ["-loop", "1", "-i", str(char["base_png"])]
        inactive_img_indices.append(1 + len(timeline) + len(inactive_img_indices))

    audio_idx = 1 + len(timeline) + len(timeline)   # after all images
    cmd += ["-i", str(ctx.master_audio())]

    # ------------------------------------------------------------------ #
    # Build filter_complex                                                 #
    # ------------------------------------------------------------------ #
    filters: list[str] = []

    # Scale background to canvas
    filters.append(f"[{bg_idx}:v]scale={W}:{H}[bg_base]")

    # Title hook drawtext
    title_text = _escape_drawtext(script.get("title_hook", ""))
    t_start = title_timing["start_sec"]
    t_end = title_timing["end_sec"]
    filters.append(
        f"[bg_base]drawtext="
        f"fontfile={_escape_ffmpeg_path(title_font)}:"
        f"text='{title_text}':"
        f"fontsize={title_style['font_size']}:"
        f"fontcolor={title_style['color']}:"
        f"borderw={title_style['stroke_width']}:"
        f"bordercolor={title_style['stroke_color']}:"
        f"x=(w-text_w)/2:y={title_box['y']}:"
        f"enable='between(t,{t_start},{t_end})'[bg_titled]"
    )
    current = "bg_titled"

    # Overlay clips and inactive speaker images per timeline item
    for i, item in enumerate(timeline):
        start = item["start_sec"]
        end = item["end_sec"]
        clip_in = clip_indices[i]
        img_in = inactive_img_indices[i]

        c_scaled = f"c{i}"
        img_scaled = f"img{i}"
        after_clip = f"bgc{i}"
        after_img = f"bgi{i}"

        filters.append(
            f"[{clip_in}:v]scale={abox['w']}:{abox['h']}[{c_scaled}]"
        )
        filters.append(
            f"[{img_in}:v]scale={ibox['w']}:{ibox['h']}[{img_scaled}]"
        )
        filters.append(
            f"[{current}][{c_scaled}]overlay="
            f"x={abox['x']}:y={abox['y']}:"
            f"enable='between(t,{start},{end})'[{after_clip}]"
        )
        filters.append(
            f"[{after_clip}][{img_scaled}]overlay="
            f"x={ibox['x']}:y={ibox['y']}:"
            f"enable='between(t,{start},{end})'[{after_img}]"
        )
        current = after_img

    # Burn subtitles
    srt_escaped = _escape_ffmpeg_path(ctx.subtitles_srt())
    fontsdir_escaped = _escape_ffmpeg_path(sub_font.parent)

    # libass uses PlayResY=288 as its internal reference height when rendering
    # SRT files.  A raw FontSize=64 at PlayResY=288 scales to
    # (64/288)×H ≈ 427 px on a 1920-tall canvas — far too large.
    # Correct mapping: libass_pts = preset_px × PlayResY / canvas_height.
    # For font_size=64 on H=1920: 64×288/1920 = 9.6 → 10 libass pts,
    # which renders as visually ≈64 px on the final 1920-tall video.
    _LIBASS_PLAY_RES_Y = 288
    libass_font_size = max(1, round(sub_style["font_size"] * _LIBASS_PLAY_RES_Y / H))

    force_style = (
        f"FontName={sub_font.stem},"
        f"FontSize={libass_font_size},"
        f"PrimaryColour=&H00FFFFFF,"
        f"OutlineColour=&H00000000,"
        f"Outline={sub_style['stroke_width']}"
    )
    filters.append(
        f"[{current}]subtitles={srt_escaped}:"
        f"fontsdir={fontsdir_escaped}:"
        f"force_style='{force_style}'[final_v]"
    )

    filter_complex = ";".join(filters)

    # ------------------------------------------------------------------ #
    # Assemble and run final FFmpeg command                                #
    # ------------------------------------------------------------------ #
    ctx.render_dir().mkdir(parents=True, exist_ok=True)
    final = ctx.final_mp4()

    cmd += [
        "-filter_complex", filter_complex,
        "-map", "[final_v]",
        "-map", f"{audio_idx}:a",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", str(preset["fps"]),
        "-c:a", "aac",
        "-t", str(total_duration),
        str(final),
    ]

    try:
        run_ffmpeg(cmd, timeout=_RENDER_TIMEOUT_SEC)
    except FFmpegError as exc:
        raise CompositorError(f"FFmpeg composition failed: {exc}") from exc

    if not final.exists():
        raise CompositorError(f"FFmpeg did not produce final video: {final}")

    actual_duration = get_media_duration(final)
    if abs(actual_duration - total_duration) > _DURATION_TOLERANCE_SEC:
        raise CompositorError(
            f"Final video duration ({actual_duration:.4f}s) deviates from "
            f"timeline ({total_duration:.4f}s) beyond tolerance"
        )

    write_render_metadata(ctx, ctx.job.output_preset, len(timeline))

    return final
