"""ElevenLabs concrete implementation of the TTSProvider interface."""
from __future__ import annotations

import wave
from pathlib import Path

from app.adapters.tts_provider_adapter import TTSError, TTSProvider


class ElevenLabsTTSProvider(TTSProvider):
    """Calls the ElevenLabs TTS API to synthesize speech per dialogue line.

    Requires ELEVENLABS_API_KEY to be set in the environment (via .env).
    Output is written as a mono WAV file at the path provided.
    """

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise TTSError(
                "ELEVENLABS_API_KEY is not set. Add it to your .env file."
            )
        try:
            from elevenlabs.client import ElevenLabs
            from elevenlabs import VoiceSettings
        except ImportError as exc:
            raise TTSError(
                "elevenlabs package is not installed. Run: pip install elevenlabs"
            ) from exc
        self._client = ElevenLabs(api_key=api_key)
        # use_speaker_boost=True raises output loudness significantly above the
        # ~-34 dB mean produced by default ElevenLabs settings.
        self._voice_settings = VoiceSettings(
            stability=0.5,
            similarity_boost=0.75,
            use_speaker_boost=True,
        )

    def synthesize(self, text: str, voice_id: str, output_path: Path) -> None:
        """Call ElevenLabs and write the result as a WAV file.

        Args:
            text: Plain spoken text to synthesize.
            voice_id: ElevenLabs voice ID (from config/voices.json).
            output_path: Destination path for the output WAV file.

        Raises:
            TTSError: on API error or file write failure.
        """
        try:
            audio = self._client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                output_format="pcm_22050",
                voice_settings=self._voice_settings,
            )
            # ElevenLabs SDK returns a generator of bytes chunks; join them.
            if isinstance(audio, (bytes, bytearray)):
                pcm_bytes = bytes(audio)
            else:
                pcm_bytes = b"".join(audio)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with wave.open(str(output_path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit signed PCM
                wf.setframerate(22050)
                wf.writeframes(pcm_bytes)

        except TTSError:
            raise
        except Exception as exc:
            raise TTSError(f"ElevenLabs synthesis failed for voice '{voice_id}': {exc}") from exc
