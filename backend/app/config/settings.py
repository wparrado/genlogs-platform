"""Centralized application settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    genlogs_env: str = "development"
    genlogs_maps_provider: str = "mock"
    genlogs_google_api_key: str = ""
    genlogs_request_timeout_seconds: int = 10


settings = Settings()
