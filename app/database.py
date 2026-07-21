"""
Configuration de la base de données
Initialisation de SQLAlchemy et gestion des sessions
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Création du moteur de base de données
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG
)

# Création de la session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base déclarative pour les modèles
Base = declarative_base()


def get_db():
    """
    Dépendance pour obtenir une session de base de données
    À utiliser dans les routes FastAPI
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialise la base de données avec toutes les tables"""
    from app.models import user, market, stage, document, history
    Base.metadata.create_all(bind=engine)
