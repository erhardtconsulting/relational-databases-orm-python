"""
Application Configuration

This module contains all configuration settings for the Notes App,
using Pydantic Settings for environment variable management and validation.
"""

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env file from project root
project_root = Path(__file__).parent.parent
env_file_path = project_root / ".env"

# Explicitly load the .env file if it exists
if env_file_path.exists():
    load_dotenv(env_file_path)


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    This class demonstrates modern Python configuration patterns
    
    Environment variables can override default values:
    - DATABASE_URL: PostgreSQL connection string
    - DEBUG: Enable debug mode
    - SECRET_KEY: Application secret key
    - HOST: Server host address
    - PORT: Server port number
    """
    
    model_config = SettingsConfigDict(
        env_file=str(env_file_path) if env_file_path.exists() else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Database Configuration
    database_url: str = Field(
        default="postgresql://notesapp:notesapp@localhost:5432/notesapp",
        description="PostgreSQL database connection URL",
        alias="DATABASE_URL"
    )
    
    # Application Configuration
    debug: bool = Field(
        default=True,
        description="Enable debug mode for development",
        alias="DEBUG"
    )
    
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for session management",
        alias="SECRET_KEY"
    )
    
    # Server Configuration
    host: str = Field(
        default="0.0.0.0",
        description="Server host address",
        alias="HOST"
    )
    
    port: int = Field(
        default=8000,
        description="Server port number",
        alias="PORT",
        ge=1,
        le=65535
    )
    
    # Application Metadata
    app_name: str = Field(
        default="Educational FastAPI Notes App",
        description="Application name for documentation"
    )
    
    app_version: str = Field(
        default="0.1.0",
        description="Application version"
    )
    
    # CORS Configuration
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins for frontend development"
    )
    
    # Database Pool Configuration
    db_pool_size: int = Field(
        default=5,
        description="Database connection pool size",
        ge=1,
        le=20
    )
    
    db_max_overflow: int = Field(
        default=10,
        description="Maximum database connection overflow",
        ge=0,
        le=50
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings with caching.
    
    Returns:
        Settings: Cached application settings instance
    """
    return Settings()


# Global settings instance for convenience
settings = get_settings()
