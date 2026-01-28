from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional, Union
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        case_sensitive=True,
        env_parse_none_str="null"
    )

    PROJECT_NAME: str = "Gestione Affitti"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/gestione_affitti"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    # Development: token dura 1 ANNO per comodità (in produzione usare 15-30 minuti)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 525600  # 365 giorni = 365 * 24 * 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 365

    # First Admin User (auto-created on first startup)
    FIRST_ADMIN_EMAIL: str = "admin@example.com"
    FIRST_ADMIN_USERNAME: str = "admin"
    FIRST_ADMIN_PASSWORD: str = "changeme123"
    FIRST_ADMIN_FULL_NAME: str = "Administrator"

    # CORS
    BACKEND_CORS_ORIGINS: Union[str, list] = ["http://localhost:3000", "http://localhost:5173"]

    # Module System
    MODULE_DIR: str = "modules"  # Relative to backend/
    MODULE_UPLOAD_DIR: str = "uploads/modules"

    # Document Parsing Services
    MRZ_SERVICE_URL: str = "http://localhost:8008"
    MRZ_SERVICE_TIMEOUT: int = 300

    # Callback URL (per servizi esterni)
    API_BASE_URL: str = "http://localhost:8000/api/v1"

    # File Storage
    STORAGE_BASE_PATH: str = "./storage"
    MAX_UPLOAD_SIZE_MB: int = 50

    # Document Job Retry
    DOCUMENT_JOB_MAX_RETRIES: int = 3
    DOCUMENT_JOB_RETRY_DELAY_SECONDS: int = 60

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


settings = Settings()
