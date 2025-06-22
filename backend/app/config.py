import os
import json
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


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
    firebase_project_id: str = Field(env="FIREBASE_PROJECT_ID")
    
    # OpenAI Configuration
    openai_api_key: str = Field(env="OPENAI_API_KEY")
    
    # Redis Configuration (using REDIS_URL from Render)
    redis_url: str = Field(env="REDIS_URL")
    
    # Cache Configuration
    topic_cache_ttl_seconds: int = Field(300, env="TOPIC_CACHE_TTL_SECONDS")
    
    # API Configuration
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000", 
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            "http://10.0.2.2:3000",
            "http://10.0.2.2:8080"
        ], 
        env="CORS_ORIGINS"
    )
    api_prefix: str = Field("/api/v1", env="API_PREFIX")
    
    @property
    def is_development(self) -> bool:
        """Check if we're in development mode"""
        return os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"
    
    @property 
    def environment(self) -> str:
        """Get environment name based on DEVELOPMENT_MODE"""
        return "development" if self.is_development else "production"
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from JSON string or return as-is if already a list"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # If not valid JSON, treat as single origin
                return [v]
        return v
    
    # External Service URLs (example)
    # external_service_url: str = Field("https://api.example.com", env="EXTERNAL_SERVICE_URL")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"  # Allow extra fields to be ignored
    }


settings = Settings()

def get_settings() -> Settings:
    """Get the application settings"""
    return settings 