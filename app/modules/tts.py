"""TTS module — generates per-line audio segments and writes manifest.json."""
from __future__ import annotations

import json
from typing import Any

from app.adapters.tts_provider_adapter import (
    TTSError,
    TTSProvider,
    resolve_voice_id,
)
from app.core.job_context import JobContext
from app.utils.ffprobe_utils import get_audio_duration


def generate_tts(
    ctx: JobContext,
    provider: TTSProvider,
    voice_mapping: dict[str, str],
) -> list[dict[str, Any]]:
    """Generate one audio segment per dialogue line and write manifest.json.

    Resolves all voice IDs before synthesis begins; fails early if any
    character has no voice mapping.  Duration is measured from the persisted
    file using ffprobe, never estimated.

    Args:
        ctx: JobContext for canonical path resolution.
        provider: TTSProvider implementation.
        voice_mapping: character_id → voice_id mapping from load_voice_mapping().

    Returns:
        The manifest as a list of dicts (matches manifest.json on disk).

    Raises:
        TTSError: if a voice mapping is missing or the provider call fails.
        RuntimeError: if ffprobe cannot measure a segment duration.
    """
    dialogue: list[dict[str, Any]] = json.loads(
        ctx.dialogue_json().read_text(encoding="utf-8")
    )

    # Resolve all voice IDs before any synthesis starts (fail-fast on missing mapping)
    voice_ids: dict[str, str] = {
        line["speaker"]: resolve_voice_id(line["speaker"], voice_mapping)
        for line in dialogue
    }

    manifest: list[dict[str, Any]] = []

    for line in dialogue:
        idx: int = line["index"]
        speaker: str = line["speaker"]
        text: str = line["text"]
        voice_id: str = voice_ids[speaker]

        segment_path = ctx.audio_segment(idx, speaker)
        print(type(text))
        print(f"Nova fala: {text} (speaker: {speaker}, voice_id: {voice_id})")
        provider.synthesize(text, voice_id, segment_path)

        if not segment_path.exists():
            raise TTSError(
                f"Provider did not write segment file: {segment_path}"
            )

        duration = get_audio_duration(segment_path)
        print(f"Duração do segmento de áudio: {duration} segundos")
        manifest.append(
            {
                "index": idx,
                "speaker": speaker,
                "text": text,
                "voice_id": voice_id,
                "audio_file": str(segment_path),
                "duration_sec": round(duration, 4),
            }
        )

    ctx.audio_manifest().write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return manifest
