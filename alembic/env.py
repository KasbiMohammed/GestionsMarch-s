"""
Alembic Environment Configuration
Configuration de l'environnement pour les migrations de base de données
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Import des modèles et de la configuration
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import settings
from app.database import Base
from app.models import user, market, stage, document, history

# this is the Alembic Config object
config = context.config

# Interpréter le fichier de configuration pour Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Ajouter l'URL de la base de données depuis les settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# MetaData target pour le support autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Exécute les migrations en mode 'offline'.
    
    Ce contexte configure uniquement un Engine
    sans connexion à la base de données.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Exécute les migrations en mode 'online'.
    
    Ce contexte configure une connexion à la base de données
    et exécute les migrations.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
