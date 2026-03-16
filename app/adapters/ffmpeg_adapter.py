"""FFmpeg adapter — centralised layer for all FFmpeg shell invocations."""
from __future__ import annotations

import subprocess
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


def convert_to_wav(
    input_path: Path,
    output_path: Path,
    sample_rate: int = 44100,
    channels: int = 1,
) -> None:
    """Convert any audio file to WAV (pcm_s16le).

    Args:
        input_path: Source audio file (e.g. MP3).
        output_path: Destination WAV file path.
        sample_rate: Output sample rate in Hz.
        channels: Number of audio channels (1 = mono).

    Raises:
        FFmpegError: if FFmpeg fails.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg(
        [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-acodec", "pcm_s16le",
            "-ar", str(sample_rate),
            "-ac", str(channels),
            str(output_path),
        ]
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


def normalize_audio(input_path: Path, output_path: Path) -> None:
    """Normalize audio loudness to -14 LUFS (YouTube/streaming standard).

    Applies the FFmpeg loudnorm filter (I=-14:TP=-1.5:LRA=11).  When
    input_path and output_path are the same, a temporary file is used to
    avoid FFmpeg's read/write conflict and then renamed into place.

    Args:
        input_path: Source audio file.
        output_path: Destination file path (may equal input_path for in-place).

    Raises:
        FFmpegError: if FFmpeg fails.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_name(output_path.stem + "_loudnorm_tmp.wav")
    try:
        run_ffmpeg(
            [
                "ffmpeg", "-y",
                "-i", str(input_path),
                "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
                "-ar", "44100",
                "-ac", "2",
                str(tmp_path),
            ]
        )
        tmp_path.replace(output_path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


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
        f"crop={width}:{height},setsar=1"
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
