"""Configuration management for KisanSathi Rajasthan using Pydantic Settings."""

from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server Configuration
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Strict CORS Security (Never allow "*")
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # Supabase & Database (Backend secrets)
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    DATABASE_URL: str = ""

    # Google Gemini LLM API
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"

    # Default model versioning
    DEFAULT_MODEL_VERSION: str = "baseline"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def allowed_origins(self) -> List[str]:
        """Parse comma-separated origins if provided, ensuring '*' is never returned."""
        origins = [orig.strip() for orig in self.FRONTEND_ORIGIN.split(",") if orig.strip()]
        # Safety enforcement against wildcard CORS
        sanitized = [orig for orig in origins if orig != "*"]
        return sanitized if sanitized else ["http://localhost:5173"]


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
