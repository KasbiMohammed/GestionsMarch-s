"""
Migration pour ajouter les tables de gestion des délais réglementaires
Conforme au Décret n°2-22-431 du 8 mars 2023
"""

from sqlalchemy import text
from app.database import engine


def upgrade():
    """Crée les tables pour la gestion des délais"""
    
    with engine.connect() as conn:
        # Table deadline_settings
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS deadline_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deadline_type VARCHAR(50) UNIQUE NOT NULL,
                type_name VARCHAR(200) NOT NULL,
                description TEXT,
                j1 INTEGER DEFAULT 30,
                j2 INTEGER DEFAULT 15,
                j3 INTEGER DEFAULT 7,
                critique INTEGER DEFAULT 3,
                activation BOOLEAN DEFAULT 1,
                default_days INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                updated_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (updated_by) REFERENCES users(id)
            )
        """))
        
        # Table deadlines
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS deadlines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deadline_type VARCHAR(50) NOT NULL,
                market_id INTEGER,
                planning_id INTEGER,
                offer_id INTEGER,
                start_date DATE NOT NULL,
                due_date DATE NOT NULL,
                completed_date DATE,
                days_remaining INTEGER DEFAULT 0,
                days_overdue INTEGER DEFAULT 0,
                alert_level VARCHAR(20) DEFAULT 'normal',
                status VARCHAR(20) DEFAULT 'actif',
                title VARCHAR(300) NOT NULL,
                description TEXT,
                reference VARCHAR(100),
                original_due_date DATE,
                extension_count INTEGER DEFAULT 0,
                extension_reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                updated_by INTEGER,
                FOREIGN KEY (market_id) REFERENCES markets(id),
                FOREIGN KEY (planning_id) REFERENCES market_plannings(id),
                FOREIGN KEY (offer_id) REFERENCES offers(id),
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (updated_by) REFERENCES users(id)
            )
        """))
        
        # Table deadline_alerts
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS deadline_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deadline_id INTEGER NOT NULL,
                alert_level VARCHAR(20) NOT NULL,
                alert_date DATETIME NOT NULL,
                acknowledged BOOLEAN DEFAULT 0,
                acknowledged_by INTEGER,
                acknowledged_at DATETIME,
                message TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (deadline_id) REFERENCES deadlines(id) ON DELETE CASCADE,
                FOREIGN KEY (acknowledged_by) REFERENCES users(id)
            )
        """))
        
        # Table deadline_notifications
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS deadline_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deadline_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                title VARCHAR(300) NOT NULL,
                message TEXT NOT NULL,
                status VARCHAR(20) DEFAULT 'en_attente',
                scheduled_date DATETIME,
                sent_date DATETIME,
                read_date DATETIME,
                notification_type VARCHAR(50) DEFAULT 'email',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (deadline_id) REFERENCES deadlines(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """))
        
        # Créer les index pour optimiser les performances
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_deadline_settings_type ON deadline_settings(deadline_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_deadlines_type ON deadlines(deadline_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_deadlines_market ON deadlines(market_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_deadlines_planning ON deadlines(planning_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_deadlines_offer ON deadlines(offer_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_deadline_alerts_deadline ON deadline_alerts(deadline_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_deadline_notifications_deadline ON deadline_notifications(deadline_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_deadline_notifications_user ON deadline_notifications(user_id)"))
        
        conn.commit()
    
    print("Migration des tables de délais terminée avec succès")


def downgrade():
    """Supprime les tables de gestion des délais"""
    
    with engine.connect() as conn:
        conn.execute(text("DROP INDEX IF EXISTS idx_deadline_notifications_user"))
        conn.execute(text("DROP INDEX IF EXISTS idx_deadline_notifications_deadline"))
        conn.execute(text("DROP INDEX IF EXISTS idx_deadline_alerts_deadline"))
        conn.execute(text("DROP INDEX IF EXISTS idx_deadlines_offer"))
        conn.execute(text("DROP INDEX IF EXISTS idx_deadlines_planning"))
        conn.execute(text("DROP INDEX IF EXISTS idx_deadlines_market"))
        conn.execute(text("DROP INDEX IF EXISTS idx_deadlines_type"))
        conn.execute(text("DROP INDEX IF EXISTS idx_deadline_settings_type"))
        
        conn.execute(text("DROP TABLE IF EXISTS deadline_notifications"))
        conn.execute(text("DROP TABLE IF EXISTS deadline_alerts"))
        conn.execute(text("DROP TABLE IF EXISTS deadlines"))
        conn.execute(text("DROP TABLE IF EXISTS deadline_settings"))
        
        conn.commit()
    
    print("Rollback de la migration des tables de délais terminé")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
