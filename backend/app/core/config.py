"""Centralized configuration. All values come from environment variables —
never hard-code secrets or per-environment config here."""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "Real Estate CRM"
    ENV: str = "development"  # development | staging | production
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Security / auth
    SECRET_KEY: str = Field(..., description="Used to sign JWTs. Required, no default.")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 48
    JWT_ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"

    # Redis / background jobs
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Rate limiting
    LOGIN_RATE_LIMIT_PER_MINUTE: int = 10
    LOGIN_LOCKOUT_THRESHOLD: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # Email (dev default: log to console; swap for real SMTP/provider via env)
    EMAIL_BACKEND: str = "console"  # console | smtp
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAIL_FROM: str = "no-reply@example.com"

    # File storage
    STORAGE_BACKEND: str = "local"  # local | s3
    STORAGE_LOCAL_PATH: str = "./storage"
    MAX_UPLOAD_SIZE_MB: int = 25

    # Feature flags (server-enforced; see core/feature_flags.py)
    FEATURE_AI: bool = False
    FEATURE_WHATSAPP: bool = False
    FEATURE_WEBHOOKS: bool = True
    FEATURE_AUTOMATIONS: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
