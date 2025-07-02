from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application Configuration
    debug: bool = Field(True, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")

    # Server Configuration
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")

    # API prefix
    api_prefix: str = ""

    # Firebase
    # The absolute path to your Firebase service account JSON file.
    # This is the standard Google Cloud env var for pointing to a service account key file.
    # This MUST be set in any environment not using the Firebase emulators.
    google_application_credentials: Optional[str] = Field(None, env="GOOGLE_APPLICATION_CREDENTIALS")
    firebase_project_id: str = Field("spaced-b571d", env="FIREBASE_PROJECT_ID")

    # Redis Configuration
    redis_url: str = Field("redis://localhost:6379", env="REDIS_URL")

    # OpenAI API Key
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")

    # Cache Configuration
    topic_cache_ttl_seconds: int = Field(300, env="TOPIC_CACHE_TTL_SECONDS")

    # CORS settings
    cors_origins: List[str] = Field(
        default=[
            "https://getspaced.app",
            "https://staging.getspaced.app",
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
        return self.debug

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
