"""
Migration pour ajouter les tables du Chatbot IA
Module dédié - Architecture RAG pour l'assistance intelligente
"""

from sqlalchemy import text
from app.database import engine


def upgrade():
    """Crée les tables pour le chatbot IA"""
    
    with engine.connect() as conn:
        # Table chat_sessions
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_name VARCHAR(200),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """))
        
        # Table chat_messages
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                message_type VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                query_type VARCHAR(20),
                sources JSON,
                confidence REAL,
                sql_query TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
            )
        """))
        
        # Table knowledge_base
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_type VARCHAR(20) NOT NULL,
                title VARCHAR(300) NOT NULL,
                description TEXT,
                content TEXT NOT NULL,
                chunk_id VARCHAR(100),
                chunk_index INTEGER,
                source VARCHAR(200),
                category VARCHAR(100),
                tags JSON,
                language VARCHAR(10) DEFAULT 'fr',
                embedding JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """))
        
        # Table document_index
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS document_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_type VARCHAR(50) NOT NULL,
                document_id INTEGER,
                title VARCHAR(300) NOT NULL,
                content TEXT NOT NULL,
                doc_metadata JSON,
                embedding JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """))
        
        # Table chatbot_feedback
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chatbot_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                rating INTEGER,
                is_helpful BOOLEAN,
                comment TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (message_id) REFERENCES chat_messages(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """))
        
        # Créer les index pour optimiser les performances
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_knowledge_base_type ON knowledge_base(document_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_knowledge_base_category ON knowledge_base(category)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_knowledge_base_source ON knowledge_base(source)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_document_index_type ON document_index(document_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_document_index_doc_id ON document_index(document_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chatbot_feedback_message ON chatbot_feedback(message_id)"))
        
        conn.commit()
    
    print("Migration des tables du chatbot terminée avec succès")


def downgrade():
    """Supprime les tables du chatbot IA"""
    
    with engine.connect() as conn:
        conn.execute(text("DROP INDEX IF EXISTS idx_chatbot_feedback_message"))
        conn.execute(text("DROP INDEX IF EXISTS idx_document_index_doc_id"))
        conn.execute(text("DROP INDEX IF EXISTS idx_document_index_type"))
        conn.execute(text("DROP INDEX IF EXISTS idx_knowledge_base_source"))
        conn.execute(text("DROP INDEX IF EXISTS idx_knowledge_base_category"))
        conn.execute(text("DROP INDEX IF EXISTS idx_knowledge_base_type"))
        conn.execute(text("DROP INDEX IF EXISTS idx_chat_messages_session"))
        conn.execute(text("DROP INDEX IF EXISTS idx_chat_sessions_user"))
        
        conn.execute(text("DROP TABLE IF EXISTS chatbot_feedback"))
        conn.execute(text("DROP TABLE IF EXISTS document_index"))
        conn.execute(text("DROP TABLE IF EXISTS knowledge_base"))
        conn.execute(text("DROP TABLE IF EXISTS chat_messages"))
        conn.execute(text("DROP TABLE IF EXISTS chat_sessions"))
        
        conn.commit()
    
    print("Rollback de la migration des tables du chatbot terminé")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
