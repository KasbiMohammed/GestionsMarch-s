"""
Migration pour ajouter les tables du Calendrier Intelligent
Module dédié - Agrégation des événements et suivi budgétaire
"""

from sqlalchemy import text
from app.database import engine


def upgrade():
    """Crée les tables pour le calendrier intelligent"""
    
    with engine.connect() as conn:
        # Table calendar_events
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_module VARCHAR(50) NOT NULL,
                source_entity_id INTEGER,
                source_entity_type VARCHAR(50),
                event_type VARCHAR(50) NOT NULL,
                title VARCHAR(300) NOT NULL,
                description TEXT,
                start_date DATETIME NOT NULL,
                end_date DATETIME,
                is_all_day BOOLEAN DEFAULT 0,
                service VARCHAR(100),
                responsible VARCHAR(100),
                procedure VARCHAR(100),
                status VARCHAR(50),
                priority VARCHAR(20),
                color VARCHAR(7),
                icon VARCHAR(50),
                doc_metadata JSON,
                is_synced BOOLEAN DEFAULT 1,
                last_synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Table budget_tracking
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS budget_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                month INTEGER,
                service VARCHAR(100),
                budget_voted REAL DEFAULT 0.0,
                budget_engaged REAL DEFAULT 0.0,
                budget_consumed REAL DEFAULT 0.0,
                budget_remaining REAL DEFAULT 0.0,
                procedure_breakdown JSON,
                total_markets INTEGER DEFAULT 0,
                total_amount REAL DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Créer les index pour optimiser les performances
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_calendar_events_source ON calendar_events(source_module, source_entity_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_calendar_events_type ON calendar_events(event_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_calendar_dates ON calendar_events(start_date, end_date)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_calendar_service ON calendar_events(service)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_calendar_responsible ON calendar_events(responsible)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_calendar_procedure ON calendar_events(procedure)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_calendar_status ON calendar_events(status)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_budget_year ON budget_tracking(year)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_budget_month ON budget_tracking(year, month)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_budget_service ON budget_tracking(year, service)"))
        
        conn.commit()
    
    print("Migration des tables du calendrier terminée avec succès")


def downgrade():
    """Supprime les tables du calendrier intelligent"""
    
    with engine.connect() as conn:
        conn.execute(text("DROP INDEX IF EXISTS idx_budget_service"))
        conn.execute(text("DROP INDEX IF EXISTS idx_budget_month"))
        conn.execute(text("DROP INDEX IF EXISTS idx_budget_year"))
        conn.execute(text("DROP INDEX IF EXISTS idx_calendar_status"))
        conn.execute(text("DROP INDEX IF EXISTS idx_calendar_procedure"))
        conn.execute(text("DROP INDEX IF EXISTS idx_calendar_responsible"))
        conn.execute(text("DROP INDEX IF EXISTS idx_calendar_service"))
        conn.execute(text("DROP INDEX IF EXISTS idx_calendar_dates"))
        conn.execute(text("DROP INDEX IF EXISTS idx_calendar_type"))
        conn.execute(text("DROP INDEX IF EXISTS idx_calendar_source"))
        
        conn.execute(text("DROP TABLE IF EXISTS budget_tracking"))
        conn.execute(text("DROP TABLE IF EXISTS calendar_events"))
        
        conn.commit()
    
    print("Rollback de la migration des tables du calendrier terminé")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
