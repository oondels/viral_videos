import os

from dotenv import load_dotenv

load_dotenv()


class _Config:
    @property
    def log_level(self) -> str:
        return os.getenv("LOG_LEVEL", "INFO").upper()

    @property
    def default_duration_sec(self) -> int:
        return int(os.getenv("DEFAULT_DURATION_SEC", "30"))

    @property
    def openai_api_key(self) -> str:
        return os.getenv("OPENAI_API_KEY", "")

    @property
    def elevenlabs_api_key(self) -> str:
        return os.getenv("ELEVENLABS_API_KEY", "")

    @property
    def google_application_credentials(self) -> str:
        return os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")


config = _Config()
