"""ElevenLabs concrete implementation of the TTSProvider interface."""
from __future__ import annotations

from pathlib import Path

from app.adapters.tts_provider_adapter import TTSError, TTSProvider


class ElevenLabsTTSProvider(TTSProvider):
    """Calls the ElevenLabs TTS API to synthesize speech per dialogue line.

    Requires ELEVENLABS_API_KEY to be set in the environment (via .env).
    The API returns MP3 data which is saved directly to the output path.
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
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
            speed=1.0,
        )

    def synthesize(self, text: str, voice_id: str, output_path: Path) -> None:
        """Call ElevenLabs and write the result as an MP3 file.

        Args:
            text: Plain spoken text to synthesize.
            voice_id: ElevenLabs voice ID (from config/voices.json).
            output_path: Destination path for the MP3 file.

        Raises:
            TTSError: on API error or file write failure.
        """
        try:
            audio = self._client.text_to_speech.convert(
                voice_id=voice_id,
                output_format="mp3_22050_32",
                text=text,
                model_id="eleven_flash_v2_5",
                voice_settings=self._voice_settings,
            )
            
            print(f"Outptut path do audio: {output_path}")
            with open(output_path, "wb") as f:
                for chunk in audio:
                    if chunk:
                        f.write(chunk)
            print(f"{output_path}: A new audio file was saved successfully!")
            output_path.parent.mkdir(parents=True, exist_ok=True)

        except TTSError:
            raise
        except Exception as exc:
            raise TTSError(f"ElevenLabs synthesis failed for voice '{voice_id}': {exc}") from exc
