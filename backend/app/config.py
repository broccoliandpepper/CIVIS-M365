"""
Configuration centrale de l'application SIEM M365
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    APP_NAME: str = "SIEM_M365"
    APP_ENV: str = "development"
    DEBUG: bool = False
    
    DB_ENCRYPTION_KEY: str = "siem-m365-secure-32byte-key!!"
    JWT_SECRET_KEY: str = "siem-m365-jwt-secret-key-2024!"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    BACKUP_ENCRYPTION_KEY: str = "siem-m365-backup-32byte-key!!"
    
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
    
    PASSWORD_MIN_LENGTH: int = 12
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
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


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()