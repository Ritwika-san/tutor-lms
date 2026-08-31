import os
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://user:password@localhost:5432/tutor_lms"
    )

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expiration_hours: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

    # Environment
    environment: Literal["development", "production", "testing"] = os.getenv(
        "ENVIRONMENT", "development"
    )
    chroma_path: str = os.getenv("CHROMA_PATH", "./chroma_data")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    doubt_similarity_threshold: float = float(os.getenv("DOUBT_SIMILARITY_THRESHOLD", "0.85"))

    # Password validation
    min_password_length: int = 8
    require_uppercase: bool = True
    require_digit: bool = True
    require_special: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
