"""TTS provider adapter — interface and voice mapping loader.

The TTSProvider interface defines one call per dialogue line.
Concrete implementations must subclass TTSProvider and override synthesize.
Voice mapping is loaded from config/voices.json at runtime.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path

_VOICES_CONFIG_PATH = Path("config") / "voices.json"


class TTSError(Exception):
    """Raised when a TTS provider call or voice mapping lookup fails."""


def load_voice_mapping(config_path: Path | None = None) -> dict[str, str]:
    """Load the character → voice_id mapping from config/voices.json.

    Args:
        config_path: Override path for testing. Defaults to config/voices.json.

    Returns:
        A dict mapping character_id to voice_id.

    Raises:
        TTSError: if the config file is missing or not valid JSON.
    """
    path = config_path or _VOICES_CONFIG_PATH
    if not path.exists():
        raise TTSError(
            f"Voice mapping config not found: {path}. "
            "Copy config/voices.example.json to config/voices.json and fill in voice ids."
        )
    try:
        mapping: dict[str, str] = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TTSError(f"Invalid JSON in voice mapping config {path}: {exc}") from exc
    return mapping


def resolve_voice_id(character: str, mapping: dict[str, str]) -> str:
    """Return the voice_id for a character, raising TTSError if not mapped.

    Args:
        character: The character id (e.g. 'char_a').
        mapping: The loaded voice mapping dict.

    Returns:
        The voice_id string.

    Raises:
        TTSError: if the character has no voice mapping.
    """
    voice_id = mapping.get(character)
    if not voice_id:
        raise TTSError(
            f"No voice mapping found for character '{character}'. "
            f"Add it to config/voices.json. Known characters: {sorted(mapping)}"
        )
    return voice_id


class TTSProvider(ABC):
    """Provider-agnostic interface for text-to-speech synthesis.

    Each call to synthesize must generate exactly one audio file
    (MP3 format preferred).
    """

    @abstractmethod
    def synthesize(self, text: str, voice_id: str, output_path: Path) -> None:
        """Convert text to speech and write the result to output_path.

        Args:
            text: The plain spoken text to synthesize.
            voice_id: The provider-specific voice identifier.
            output_path: Destination path for the audio file.

        Raises:
            TTSError: if synthesis fails or the provider returns an error.
        """
