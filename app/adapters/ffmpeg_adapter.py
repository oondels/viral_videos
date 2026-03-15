"""FFmpeg adapter — centralised layer for all FFmpeg shell invocations."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

_FFMPEG_TIMEOUT_SEC = 120


class FFmpegError(Exception):
    """Raised when an FFmpeg command exits with a non-zero status."""


def run_ffmpeg(args: list[str], timeout: int = _FFMPEG_TIMEOUT_SEC) -> None:
    """Run an FFmpeg command and raise FFmpegError on failure.

    Args:
        args: Full argument list starting with 'ffmpeg'.
        timeout: Maximum seconds to wait before killing the process.

    Raises:
        FFmpegError: if the process exits with a non-zero code.
    """
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise FFmpegError(
            f"FFmpeg failed (exit {result.returncode}): {result.stderr.strip()}"
        )


def concat_audio(input_paths: list[Path], output_path: Path) -> None:
    """Concatenate audio files in order using the concat demuxer.

    All inputs must share the same sample rate and channel layout.
    A temporary concat list file is written alongside the output.

    Args:
        input_paths: Ordered list of input audio file paths.
        output_path: Destination file path for the concatenated audio.

    Raises:
        FFmpegError: if FFmpeg fails.
        ValueError: if input_paths is empty.
    """
    if not input_paths:
        raise ValueError("concat_audio requires at least one input file")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    concat_list = output_path.parent / "concat_list.txt"
    list_lines = [f"file '{p.resolve()}'" for p in input_paths]
    concat_list.write_text("\n".join(list_lines), encoding="utf-8")

    run_ffmpeg(
        [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            str(output_path),
        ]
    )


def scale_and_trim_video(
    input_path: Path,
    output_path: Path,
    width: int,
    height: int,
    duration_sec: float,
    loop: bool = False,
) -> None:
    """Scale a video to cover the target canvas, crop, and trim to duration.

    Uses scale-to-cover + crop to avoid letterboxing.  Strips the audio
    track so the output is video-only.

    Args:
        input_path: Source video file.
        output_path: Destination file path.
        width: Target canvas width in pixels.
        height: Target canvas height in pixels.
        duration_sec: Output duration in seconds.
        loop: If True, loop the source before trimming (for short sources).

    Raises:
        FFmpegError: if FFmpeg fails.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    scale_filter = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height}"
    )

    cmd = ["ffmpeg", "-y"]
    if loop:
        cmd += ["-stream_loop", "-1"]
    cmd += [
        "-i", str(input_path),
        "-vf", scale_filter,
        "-t", str(duration_sec),
        "-an",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        str(output_path),
    ]
    run_ffmpeg(cmd)
