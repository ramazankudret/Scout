"""
Scout Core Configuration Module.

Uses Pydantic Settings for type-safe environment variable loading.
All configuration is loaded from environment variables or .env file.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Scout"
    app_version: str = "0.1.0"
    debug: bool = True
    environment: Literal["development", "staging", "production"] = "development"

    # API
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Database
    database_url: str = "postgresql+asyncpg://scout:scout_secure_2024@localhost/scout_db"
    
    # Security
    secret_key: str = "CHANGE_THIS_IN_PRODUCTION_SECRET_KEY_12345"
    access_token_expire_minutes: int = 60 * 24 * 8 # 8 days
    algorithm: str = "HS256"
    
    # LLM Settings
    redis_url: str = "redis://localhost:6379/0"

    # LLM Configuration - Multi-Model Strategy
    llm_provider: Literal["ollama", "openai", "local"] = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    
    # Model Fleet
    ollama_model: str = "llama3.1:8b"              # Default: Balanced performance
    ollama_reasoning_model: str = "deepseek-r1:8b" # Deep thinking, threat analysis
    ollama_fast_model: str = "nemotron-mini:4b"    # RTX optimized, agent routing
    
    # Model Selection Strategy
    # - reasoning: Complex threat analysis, incident investigation, report generation
    # - fast: Agent routing, simple decisions, real-time responses
    # - default: General tasks, fallback
    
    openai_api_key: str | None = None

    # Security
    secret_key: str = "dev-secret-key-change-in-production"

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "console"] = "console"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Global settings instance (for convenience)
settings = get_settings()
