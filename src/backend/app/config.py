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
    # redis_url: str = Field("redis://localhost:6379", env="REDIS_URL")  # Commented out Redis

    # OpenAI API Key
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4o", env="OPENAI_MODEL")

    # Feature Flags
    use_combined_llm: bool = Field(False, env="USE_COMBINED_LLM")
    use_responses_api: bool = Field(True, env="USE_RESPONSES_API")

    # OpenAI request settings
    openai_request_timeout_seconds: int = Field(12, env="OPENAI_REQUEST_TIMEOUT_SECONDS")
    openai_max_retries: int = Field(2, env="OPENAI_MAX_RETRIES")

    # Anthropic Configuration
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field("claude-sonnet-4-20250514", env="ANTHROPIC_MODEL")
    anthropic_fast_model: str = Field("claude-3-5-haiku-latest", env="ANTHROPIC_FAST_MODEL")
    anthropic_request_timeout_seconds: int = Field(30, env="ANTHROPIC_REQUEST_TIMEOUT_SECONDS")
    anthropic_max_retries: int = Field(2, env="ANTHROPIC_MAX_RETRIES")
    use_anthropic: bool = Field(True, env="USE_ANTHROPIC")

    # Cartesia API Key for TTS
    cartesia_api_key: Optional[str] = Field(None, env="CARTESIA_API_KEY")

    # LiveKit Configuration
    livekit_api_key: Optional[str] = Field(None, env="LIVEKIT_API_KEY")
    livekit_api_secret: Optional[str] = Field(None, env="LIVEKIT_API_SECRET")
    livekit_server_url: str = Field("wss://your-livekit-server.livekit.cloud", env="LIVEKIT_SERVER_URL")

    # Deepgram API Key for STT (alternative to OpenAI Whisper)
    deepgram_api_key: Optional[str] = Field(None, env="DEEPGRAM_API_KEY")

    # Cache Configuration
    topic_cache_ttl_seconds: int = Field(300, env="TOPIC_CACHE_TTL_SECONDS")

    # CORS settings - raw string from env, parsed below
    cors_origins_raw: str = Field(
        default="",
        alias="CORS_ORIGINS",
    )

    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string, JSON array, or use defaults."""
        default_origins = [
            "https://getspaced.app",
            "https://www.getspaced.app",
            "https://app.getspaced.app",
            "https://staging.getspaced.app",
            "https://api.getspaced.app",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
        ]

        if not self.cors_origins_raw:
            return default_origins

        raw = self.cors_origins_raw.strip()
        if raw.startswith("["):
            # JSON array
            import json

            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return default_origins

        # Comma-separated string
        origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
        return origins if origins else default_origins

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
