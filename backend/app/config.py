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

    # Firebase Configuration
    firebase_service_account_path: Optional[str] = Field(None, env="FIREBASE_SERVICE_ACCOUNT_PATH")
    firebase_service_account_json: Optional[str] = Field(None, env="FIREBASE_SERVICE_ACCOUNT_JSON")
    firebase_project_id: str = Field(..., env="FIREBASE_PROJECT_ID")
    firebase_private_key_id: str = Field(..., env="FIREBASE_PRIVATE_KEY_ID")
    # Replace newlines with actual newline characters for the private key
    firebase_private_key: str = Field(..., env="FIREBASE_PRIVATE_KEY")
    firebase_client_email: str = Field(..., env="FIREBASE_CLIENT_EMAIL")
    firebase_client_id: str = Field(..., env="FIREBASE_CLIENT_ID")
    firebase_auth_uri: str = Field("https://accounts.google.com/o/oauth2/auth", env="FIREBASE_AUTH_URI")
    firebase_token_uri: str = Field("https://oauth2.googleapis.com/token", env="FIREBASE_TOKEN_URI")
    firebase_auth_provider_cert_url: str = Field(
        "https://www.googleapis.com/oauth2/v1/certs", env="FIREBASE_AUTH_PROVIDER_CERT_URL"
    )
    firebase_client_cert_url: str = Field(..., env="FIREBASE_CLIENT_CERT_URL")

    # OpenAI Configuration
    openai_api_key: str = Field(env="OPENAI_API_KEY")

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

    api_prefix: str = ""

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
