from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    gnani_api_key: str = ""
    gnani_stt_url: str = ""
    gnani_stt_model: str = "prisma-v3.0"
    gnani_stt_format: str = "codemix"
    gnani_stt_keyterms: bool = False
    gnani_tts_url: str = ""
    gnani_tts_model: str = "timbre-v2.5"
    gnani_tts_voice: str = "Nalini"
    gnani_max_concurrent: int = 1

    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = "gnani-evon-v3.3"
    llm_min_confidence: float = 0.5
    llm_timeout_sec: float = 180

    gnani_mock: bool = False

    max_upload_mb: int = 100
    max_audio_sec: int = 180
    credit_guard_seconds: float = 0

    database_url: str = "sqlite:///./bolkecheck.db"
    cors_origins: str = "http://localhost:5173"
    media_dir: Path = REPO_ROOT / "media"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
