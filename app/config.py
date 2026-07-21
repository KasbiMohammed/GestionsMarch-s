"""
Configuration de l'application
Gestion des variables d'environnement et des paramètres globaux
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Configuration principale de l'application"""
    
    # Application
    APP_NAME: str = "Gestion des Marchés Publics"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./marches_publics.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    
    # PMMP Portal
    PMMP_BASE_URL: str = "https://www.marchespublics.gov.ma"
    
    # Backup
    BACKUP_DIR: str = "backups"
    BACKUP_RETENTION_DAYS: int = 30
    
    # Logging
    LOG_DIR: str = "logs"
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Création des répertoires nécessaires
def create_directories():
    """Crée les répertoires nécessaires s'ils n'existent pas"""
    settings = Settings()
    directories = [
        settings.UPLOAD_DIR,
        settings.BACKUP_DIR,
        settings.LOG_DIR,
        "app/static/css",
        "app/static/js",
        "app/static/img",
        "app/templates",
        "app/templates/auth",
        "app/templates/markets",
        "app/templates/stages",
        "app/templates/dashboard",
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


# Instance globale des settings
settings = Settings()

# Créer les répertoires au démarrage
create_directories()
