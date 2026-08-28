"""
app/config.py
─────────────
Centralised settings loaded from .env via pydantic-settings.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM
    groq_api_key: str = ""
    groq_model_agents: str = "llama-3.3-70b-versatile"
    groq_model_judge: str = "llama-3.3-70b-versatile"

    # Sarvam TTS
    sarvam_api_key: str = ""
    sarvam_tts_url: str = "https://api.sarvam.ai/text-to-speech"

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/evaluations.db"

    # Uploads
    upload_dir: Path = Path("data/uploads")
    max_file_size_mb: int = 20

    # Logging
    log_level: str = "INFO"

    # Derived
    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    def ensure_dirs(self) -> None:
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        Path("data").mkdir(exist_ok=True)
        Path("data/audio").mkdir(exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    s = Settings()
    s.ensure_dirs()
    return s
