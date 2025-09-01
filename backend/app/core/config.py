"""Application configuration management."""

import os
from enum import Enum
from typing import Literal

from pydantic_settings import BaseSettings
from pydantic import Field


class LookupSource(str, Enum):
    """Available lookup sources."""
    SHEETS = "sheets"
    POSTGRES = "postgres"


class LookupPolicy(str, Enum):
    """Lookup policies."""
    STRICT = "strict"
    FALLBACK = "fallback"


class PDFStorage(str, Enum):
    """PDF storage backends."""
    LOCAL = "local"
    S3 = "s3"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    
    # Telegram Configuration
    tg_bot_token: str = Field(..., env="TG_BOT_TOKEN")
    tg_manager_chat_id: str = Field(..., env="TG_MANAGER_CHAT_ID")
    
    # Lookup Configuration
    lookup_source: LookupSource = Field(LookupSource.SHEETS, env="LOOKUP_SOURCE")
    lookup_policy: LookupPolicy = Field(LookupPolicy.STRICT, env="LOOKUP_POLICY")
    
    # Google Sheets Configuration
    sheets_id: str = Field("", env="SHEETS_ID")
    sheets_tab: str = Field("QuoteCatalog", env="SHEETS_TAB")
    
    # Postgres Configuration
    db_dsn: str = Field("", env="DB_DSN")
    
    # PDF Storage Configuration
    pdf_storage: PDFStorage = Field(PDFStorage.LOCAL, env="PDF_STORAGE")
    
    # S3 Configuration
    s3_endpoint: str = Field("", env="S3_ENDPOINT")
    s3_bucket: str = Field("", env="S3_BUCKET")
    s3_key: str = Field("", env="S3_KEY")
    s3_secret: str = Field("", env="S3_SECRET")
    
    # Application Configuration
    base_url: str = Field("http://localhost:8000", env="BASE_URL")
    hash_salt: str = Field("", env="HASH_SALT")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # PDF Storage Path
    pdf_dir: str = Field("pdf", env="PDF_DIR")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings