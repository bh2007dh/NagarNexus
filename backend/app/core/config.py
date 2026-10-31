import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BASE_DIR.parent


class Settings(BaseSettings):
    APP_NAME: str = "NagarNexus – AI-Powered Hyperlocal Urban Intelligence and Prediction Platform"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Database: Supports PostgreSQL in production and SQLite as local dev fallback
    DATABASE_URL: str = f"sqlite:///{(BASE_DIR / 'nagarnexus.db').as_posix()}"

    # JWT Authentication
    JWT_SECRET_KEY: str = "nagarnexus-production-grade-secret-key-2026-urban-intelligence-platform"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Storage directories
    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    PROCESSED_DIR: str = str(PROJECT_ROOT / "datasets" / "processed")
    RAW_DATASETS_DIR: str = str(PROJECT_ROOT / "datasets" / "raw")
    SAMPLE_DIR: str = str(PROJECT_ROOT / "datasets" / "sample")
    REPORTS_DIR: str = str(BASE_DIR / "generated_reports")
    MODELS_DIR: str = str(PROJECT_ROOT / "ml_models" / "trained")
    EVALUATION_DIR: str = str(PROJECT_ROOT / "ml_models" / "evaluation")
    MAX_UPLOAD_SIZE_MB: int = 50

    # External APIs
    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1"
    OPEN_METEO_ARCHIVE_URL: str = "https://archive-api.open-meteo.com/v1"
    OPENAQ_BASE_URL: str = "https://api.openaq.org/v2"
    OPENAQ_API_KEY: str = ""
    NOMINATIM_BASE_URL: str = "https://nominatim.openstreetmap.org"
    NOMINATIM_USER_AGENT: str = "NagarNexus-UrbanIntelligence/1.0"
    DATA_GOV_IN_API_KEY: str = ""

    # Optional LLM Configuration
    LLM_PROVIDER: str = "none"
    LLM_API_KEY: str = ""

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    def ensure_directories(self) -> None:
        for path_str in [
            self.UPLOAD_DIR,
            self.PROCESSED_DIR,
            self.RAW_DATASETS_DIR,
            self.SAMPLE_DIR,
            self.REPORTS_DIR,
            self.MODELS_DIR,
            self.EVALUATION_DIR,
        ]:
            os.makedirs(path_str, exist_ok=True)


settings = Settings()
settings.ensure_directories()

