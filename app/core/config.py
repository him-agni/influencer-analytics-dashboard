"""
Application configuration using pydantic-settings.
Reads from .env file and environment variables.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation and defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Database ──────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/influencer_db"

    # ── YouTube API ───────────────────────────────────────────
    youtube_api_key: str = ""

    # ── Scheduler ─────────────────────────────────────────────
    scheduler_enabled: bool = True
    scheduler_interval_hours: int = 24

    # ── Sentiment Analysis ────────────────────────────────────
    sentiment_enabled: bool = True
    sentiment_model: str = "distilbert-base-uncased-finetuned-sst-2-english"

    # ── API Server ────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "Influencer Analytics Dashboard"
    api_version: str = "1.0.0"

    # ── Data Collection Defaults ──────────────────────────────
    max_videos_per_channel: int = 50
    max_comments_per_video: int = 100

    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite backend."""
        return "sqlite" in self.database_url

    @property
    def is_postgres(self) -> bool:
        """Check if using PostgreSQL backend."""
        return "postgresql" in self.database_url


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
