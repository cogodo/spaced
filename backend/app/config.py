import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Application Configuration
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(True, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # Server Configuration
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    
    # Firebase Configuration
    firebase_service_account_path: Optional[str] = Field(None, env="FIREBASE_SERVICE_ACCOUNT_PATH")
    firebase_service_account_json: Optional[str] = Field(None, env="FIREBASE_SERVICE_ACCOUNT_JSON")
    firebase_project_id: str = Field(env="FIREBASE_PROJECT_ID")
    
    # OpenAI Configuration
    openai_api_key: str = Field(env="OPENAI_API_KEY")
    
    redis_host: str = Field(env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")
    redis_db: int = Field(0, env="REDIS_DB")
    redis_password: Optional[str] = Field(None, env="REDIS_PASSWORD")
    
    # Cache Configuration
    topic_cache_ttl_seconds: int = Field(300, env="TOPIC_CACHE_TTL_SECONDS")
    
    # API Configuration
    cors_origins: list = Field(["*"], env="CORS_ORIGINS")
    api_prefix: str = Field("/api/v1", env="API_PREFIX")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"  # Allow extra fields to be ignored
    }


settings = Settings()

def get_settings() -> Settings:
    """Get the application settings"""
    return settings 