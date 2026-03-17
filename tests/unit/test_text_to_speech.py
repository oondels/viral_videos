from app.adapters.elevenlabs_tts_adapter import ElevenLabsTTSProvider
from app.config import config

tts = ElevenLabsTTSProvider(api_key=config.elevenlabs_api_key)

tts.synthesize(
    text="Este é um exemplo de texto para fala usando a API da ElevenLabs.",
    voice_id="oJebhZNaPllxk6W0LSBA",  # Example voice ID from config/voices.json
    output_path="output/test_tts.mp3",)
