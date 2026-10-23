# Purpose: Application configuration and environment variable loading for Resit Saya.
# Security: Enforces minimum key strength in production; keeps security timeouts and limits centralized.

from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core secrets & mode
    SECRET_KEY: str = "change-me-to-a-very-secure-random-secret-key-32-bytes-minimum"
    DEV_MODE: bool = True

    # Database connection
    DATABASE_URL: str = "sqlite:///./resitsaya.db"

    # File uploads & storage
    UPLOAD_DIR: str = "../uploads"
    MAX_UPLOAD_MB: int = 10

    # Business timezone & currency
    APP_TIMEZONE: str = "Asia/Kuala_Lumpur"
    DEFAULT_CURRENCY: str = "MYR"

    # Soft delete retention
    RETENTION_DAYS: int = 30

    # Sessions and cookies
    COOKIE_NAME: str = "resitsaya_session"
    COOKIE_SECURE: bool = False
    SESSION_DAYS: int = 7

    # Rate limiting (failed login attempts)
    LOGIN_RATE_LIMIT_ATTEMPTS: int = 5
    LOGIN_RATE_LIMIT_WINDOW_MINUTES: int = 15

    # Application metadata
    APP_VERSION: str = "1.0.0"

    @property
    def upload_path(self) -> Path:
        """Resolve upload directory path reliably."""
        p = Path(self.UPLOAD_DIR)
        if not p.is_absolute():
            # Resolve relative to the backend folder (parent of app/)
            backend_dir = Path(__file__).resolve().parent.parent
            return (backend_dir / p).resolve()
        return p.resolve()

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if not self.DEV_MODE:
            if (
                not self.SECRET_KEY
                or "change-me" in self.SECRET_KEY
                or len(self.SECRET_KEY) < 32
            ):
                raise ValueError(
                    "Production security failure: SECRET_KEY must be set to a secure string "
                    "with at least 32 characters when DEV_MODE=false."
                )
        return self


settings = Settings()
