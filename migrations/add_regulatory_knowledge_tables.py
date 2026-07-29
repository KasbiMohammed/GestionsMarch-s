"""
Migration pour ajouter les tables de la Base de connaissances réglementaire
Module dédié - Importation et indexation des documents officiels
"""

from sqlalchemy import text
from app.database import engine


def upgrade():
    """Crée les tables pour la base de connaissances réglementaire"""
    
    with engine.connect() as conn:
        # Table regulatory_documents
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS regulatory_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_type VARCHAR(50) NOT NULL,
                reference VARCHAR(100) NOT NULL UNIQUE,
                title VARCHAR(500) NOT NULL,
                description TEXT,
                publication_date DATETIME,
                effective_date DATETIME,
                issuer VARCHAR(200),
                url VARCHAR(500),
                content TEXT,
                file_path VARCHAR(500),
                is_active BOOLEAN DEFAULT 1,
                version VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """))
        
        # Table regulatory_chapters
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS regulatory_chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chapter_number VARCHAR(50),
                title VARCHAR(500) NOT NULL,
                description TEXT,
                parent_chapter_id INTEGER,
                order_index INTEGER DEFAULT 0,
                content TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES regulatory_documents(id) ON DELETE CASCADE,
                FOREIGN KEY (parent_chapter_id) REFERENCES regulatory_chapters(id)
            )
        """))
        
        # Table regulatory_articles
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS regulatory_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter_id INTEGER,
                document_id INTEGER NOT NULL,
                article_number VARCHAR(50) NOT NULL,
                title VARCHAR(500),
                content TEXT NOT NULL,
                keywords JSON,
                themes JSON,
                related_articles JSON,
                doc_references JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chapter_id) REFERENCES regulatory_chapters(id) ON DELETE CASCADE,
                FOREIGN KEY (document_id) REFERENCES regulatory_documents(id)
            )
        """))
        
        # Table regulatory_keywords
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS regulatory_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Table regulatory_document_keywords
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS regulatory_document_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                keyword_id INTEGER NOT NULL,
                relevance_score REAL DEFAULT 1.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES regulatory_documents(id) ON DELETE CASCADE,
                FOREIGN KEY (keyword_id) REFERENCES regulatory_keywords(id)
            )
        """))
        
        # Table regulatory_document_themes
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS regulatory_document_themes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                theme VARCHAR(50) NOT NULL,
                relevance_score REAL DEFAULT 1.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES regulatory_documents(id) ON DELETE CASCADE
            )
        """))
        
        # Table regulatory_article_links
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS regulatory_article_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_article_id INTEGER NOT NULL,
                target_article_id INTEGER NOT NULL,
                link_type VARCHAR(50) NOT NULL,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (source_article_id) REFERENCES regulatory_articles(id),
                FOREIGN KEY (target_article_id) REFERENCES regulatory_articles(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """))
        
        # Créer les index pour optimiser les performances
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_regulatory_docs_type ON regulatory_documents(document_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_regulatory_docs_reference ON regulatory_documents(reference)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_regulatory_docs_active ON regulatory_documents(is_active)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_regulatory_chapters_doc ON regulatory_chapters(document_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_regulatory_chapters_parent ON regulatory_chapters(parent_chapter_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_regulatory_articles_doc ON regulatory_articles(document_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_regulatory_articles_chapter ON regulatory_articles(chapter_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_regulatory_articles_number ON regulatory_articles(article_number)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_regulatory_keywords_keyword ON regulatory_keywords(keyword)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_regulatory_doc_keywords_doc ON regulatory_document_keywords(document_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_regulatory_doc_keywords_kw ON regulatory_document_keywords(keyword_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_regulatory_doc_themes_doc ON regulatory_document_themes(document_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_regulatory_doc_themes_theme ON regulatory_document_themes(theme)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_regulatory_article_links_source ON regulatory_article_links(source_article_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_regulatory_article_links_target ON regulatory_article_links(target_article_id)"))
        
        conn.commit()
    
    print("Migration des tables de la base de connaissances réglementaire terminée avec succès")


def downgrade():
    """Supprime les tables de la base de connaissances réglementaire"""
    
    with engine.connect() as conn:
        conn.execute(text("DROP INDEX IF EXISTS idx_regulatory_article_links_target"))
        conn.execute(text("DROP INDEX IF EXISTS idx_regulatory_article_links_source"))
        conn.execute(text("DROP INDEX IF EXISTS idx_regulatory_doc_themes_theme"))
        conn.execute(text("DROP INDEX IF EXISTS idx_regulatory_doc_themes_doc"))
        conn.execute(text("DROP INDEX IF EXISTS idx_regulatory_doc_keywords_kw"))
        conn.execute(text("DROP INDEX IF EXISTS idx_regulatory_doc_keywords_doc"))
        conn.execute(text("DROP INDEX IF EXISTS idx_regulatory_keywords_keyword"))
        conn.execute(text("DROP INDEX IF EXISTS idx_regulatory_articles_number"))
        conn.execute(text("DROP INDEX IF EXISTS idx_regulatory_articles_chapter"))
        conn.execute(text("DROP INDEX IF EXISTS idx_regulatory_articles_doc"))
        conn.execute(text("DROP INDEX IF EXISTS idx_regulatory_chapters_parent"))
        conn.execute(text("DROP INDEX IF EXISTS idx_regulatory_chapters_doc"))
        conn.execute(text("DROP INDEX IF EXISTS idx_regulatory_docs_active"))
        conn.execute(text("DROP INDEX IF EXISTS idx_regulatory_docs_reference"))
        conn.execute(text("DROP INDEX IF EXISTS idx_regulatory_docs_type"))
        
        conn.execute(text("DROP TABLE IF EXISTS regulatory_article_links"))
        conn.execute(text("DROP TABLE IF EXISTS regulatory_document_themes"))
        conn.execute(text("DROP TABLE IF EXISTS regulatory_document_keywords"))
        conn.execute(text("DROP TABLE IF EXISTS regulatory_keywords"))
        conn.execute(text("DROP TABLE IF EXISTS regulatory_articles"))
        conn.execute(text("DROP TABLE IF EXISTS regulatory_chapters"))
        conn.execute(text("DROP TABLE IF EXISTS regulatory_documents"))
        
        conn.commit()
    
    print("Rollback de la migration des tables de la base de connaissances réglementaire terminé")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
