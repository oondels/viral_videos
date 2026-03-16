"""ElevenLabs concrete implementation of the TTSProvider interface."""
from __future__ import annotations

from pathlib import Path

from app.adapters.ffmpeg_adapter import FFmpegError, convert_to_wav
from app.adapters.tts_provider_adapter import TTSError, TTSProvider


class ElevenLabsTTSProvider(TTSProvider):
    """Calls the ElevenLabs TTS API to synthesize speech per dialogue line.

    Requires ELEVENLABS_API_KEY to be set in the environment (via .env).
    The API returns MP3 data which is converted to mono WAV (pcm_s16le,
    44100 Hz) before being written to the output path.
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
        """Call ElevenLabs and write the result as a mono WAV file.

        The API returns MP3 data which is saved to a temporary file and then
        converted to mono WAV (pcm_s16le, 44100 Hz) via FFmpeg.

        Args:
            text: Plain spoken text to synthesize.
            voice_id: ElevenLabs voice ID (from config/voices.json).
            output_path: Destination path for the mono WAV file.

        Raises:
            TTSError: on API error, file write failure, or conversion failure.
        """
        tmp_mp3 = output_path.with_suffix(".mp3")
        try:
            audio = self._client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
                voice_settings=self._voice_settings,
            )
            # ElevenLabs SDK returns a generator of bytes chunks; join them.
            if isinstance(audio, (bytes, bytearray)):
                mp3_bytes = bytes(audio)
            else:
                mp3_bytes = b"".join(audio)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_mp3.write_bytes(mp3_bytes)

            convert_to_wav(tmp_mp3, output_path, sample_rate=44100, channels=1)

        except (TTSError, FFmpegError):
            raise
        except Exception as exc:
            raise TTSError(f"ElevenLabs synthesis failed for voice '{voice_id}': {exc}") from exc
        finally:
            if tmp_mp3.exists():
                tmp_mp3.unlink(missing_ok=True)
