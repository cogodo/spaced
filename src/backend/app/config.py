import os
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application Configuration - Use DEVELOPMENT_MODE instead of ENVIRONMENT
    debug: bool = Field(True, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")

    # Server Configuration
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")

    # API prefix
    api_prefix: str = ""

    # Firebase
    firebase_service_account_json: Optional[str] = Field(None, env="FIREBASE_SERVICE_ACCOUNT_JSON")
    firebase_project_id: str = Field(..., env="FIREBASE_PROJECT_ID")

    # Redis Configuration (using REDIS_URL from Render)
    redis_url: str = Field(env="REDIS_URL")

    # Cache Configuration
    topic_cache_ttl_seconds: int = Field(300, env="TOPIC_CACHE_TTL_SECONDS")

    # CORS settings
    cors_origins: List[str] = Field(
        default=[
            "https://getspaced.app",
            "https://api.getspaced.app",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
        ],
        env="CORS_ORIGINS",
    )

    @property
    def is_development(self) -> bool:
        """Check if we're in development mode"""
        # Use DEBUG env var (which is already set) or explicit DEVELOPMENT_MODE
        return os.getenv("DEVELOPMENT_MODE", "false").lower() == "true" or os.getenv("DEBUG", "false").lower() == "true"

    @property
    def environment(self) -> str:
        """Get environment name based on DEVELOPMENT_MODE"""
        return "development" if self.is_development else "production"

    @property
    def is_production(self) -> bool:
        """Check if we're in production mode"""
        return not self.is_development

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",  # Allow extra fields to be ignored
    }


settings = Settings()


def get_settings() -> Settings:
    """Get the application settings"""
    return settings
    return settings
