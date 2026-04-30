"""
Configuration centrale de l'application SIEM M365
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "SIEM_M365"
    APP_ENV: str = "development"
    DEBUG: bool = False

    DB_ENCRYPTION_KEY: str = Field(..., min_length=32)
    JWT_SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    BACKUP_ENCRYPTION_KEY: str = Field(..., min_length=32)

    DB_PATH: str = "./data/db/siem_hot.db"
    DB_ARCHIVE_PATH: str = "./data/db/siem_archive.db"
    DB_CONFIG_PATH: str = "./data/db/siem_config.db"

    BACKUP_PATH: str = "./data/backups"
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_RETENTION_MAX_FILES: int = 30
    ROLLBACK_RETENTION_DAYS: int = 14
    ROLLBACK_RETENTION_MAX_SNAPSHOTS: int = 20

    HOST: str = "127.0.0.1"
    PORT: int = 5000

    CORS_ALLOWED_ORIGINS: str = "http://127.0.0.1:5000,http://localhost:5000"

    PASSWORD_MIN_LENGTH: int = 12
    PASSWORD_REQUIRE_SPECIAL: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def db_paths(self) -> dict:
        return {
            "hot": self.DB_PATH,
            "archive": self.DB_ARCHIVE_PATH,
            "config": self.DB_CONFIG_PATH
        }

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()