"""Centralized application settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    genlogs_env: str = "development"
    genlogs_maps_provider: str = "mock"
    genlogs_google_api_key: str = ""
    # When true, tests may prefer the local mock provider for deterministic
    # behavior when both place ids are mock:*. Production defaults to False.
    genlogs_prefer_mock_for_mock_ids: bool = False
    genlogs_request_timeout_seconds: int = 10
    genlogs_rate_limit: str = "100/minute"
    genlogs_database_url: str = "postgresql://localhost:5432/genlogs"
    genlogs_cache_cities_ttl_seconds: int = 3600
    genlogs_cache_search_ttl_seconds: int = 900
    genlogs_cache_max_size: int = 256


settings = Settings()
