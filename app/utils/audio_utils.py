"""Audio utilities for creating test fixtures and minimal WAV operations."""
from __future__ import annotations

import array
import wave
from pathlib import Path


def write_silence_wav(
    path: Path,
    duration_sec: float = 1.0,
    sample_rate: int = 22050,
) -> None:
    """Write a silent mono 16-bit PCM WAV file.

    Used in tests to produce a real, readable WAV without calling a TTS provider.

    Args:
        path: Destination file path.
        duration_sec: Duration of the silence in seconds.
        sample_rate: Sample rate in Hz.
    """
    n_samples = int(duration_sec * sample_rate)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(array.array("h", [0] * n_samples).tobytes())
