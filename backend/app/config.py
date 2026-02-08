from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = "postgresql+asyncpg://localhost/fivec_menu"
    timezone: str = "America/Los_Angeles"

    model_config = {"env_prefix": "FIVEC_"}


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
