"""
Modèles pour la Base de connaissances réglementaire
Module dédié - Importation et indexation des documents officiels
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from enum import Enum
import enum

from app.database import Base


class DocumentType(str, enum.Enum):
    """Types de documents réglementaires"""
    DECRET = "decret"
    LOI = "loi"
    ARRETE = "arrete"
    CIRCULAIRE = "circulaire"
    NOTE = "note"
    GUIDE = "guide"
    CCAG = "ccag"
    AUTRE = "autre"


class Theme(str, enum.Enum):
    """Thèmes réglementaires"""
    PLANIFICATION = "planification"
    PREPARATION = "preparation"
    PUBLICITE = "publicite"
    COMMISSION = "commission"
    ATTRIBUTION = "attribution"
    EXECUTION = "execution"
    RECEPTION = "reception"
    PAIEMENT = "paiement"
    BUDGET = "budget"
    CONTROLE = "controle"
    CONTENTIEUX = "contentieux"
    GENERAL = "general"


class RegulatoryDocument(Base):
    """Document réglementaire principal"""
    __tablename__ = "regulatory_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Informations du document
    document_type = Column(String(50), nullable=False, index=True)  # DocumentType
    reference = Column(String(100), nullable=False, unique=True, index=True)  # Référence officielle (ex: "2.22.431")
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    # Métadonnées
    publication_date = Column(DateTime, nullable=True)
    effective_date = Column(DateTime, nullable=True)
    issuer = Column(String(200), nullable=True)  # Ministère ou autorité émettrice
    url = Column(String(500), nullable=True)  # Lien vers le document officiel
    
    # Contenu
    content = Column(Text, nullable=True)  # Contenu complet du document
    file_path = Column(String(500), nullable=True)  # Chemin du fichier si stocké localement
    
    # Statut
    is_active = Column(Boolean, default=True)
    version = Column(String(50), nullable=True)  # Version du document
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relations
    chapters = relationship("Chapter", back_populates="document", cascade="all, delete-orphan")
    keywords = relationship("DocumentKeyword", back_populates="document", cascade="all, delete-orphan")
    themes = relationship("DocumentTheme", back_populates="document", cascade="all, delete-orphan")


class Chapter(Base):
    """Chapitre d'un document réglementaire"""
    __tablename__ = "regulatory_chapters"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("regulatory_documents.id"), nullable=False, index=True)
    
    # Informations du chapitre
    chapter_number = Column(String(50), nullable=True)  # Numéro du chapitre
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    # Structure hiérarchique
    parent_chapter_id = Column(Integer, ForeignKey("regulatory_chapters.id"), nullable=True)
    order_index = Column(Integer, default=0)  # Ordre d'affichage
    
    # Contenu
    content = Column(Text, nullable=True)
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    document = relationship("RegulatoryDocument", back_populates="chapters")
    parent_chapter = relationship("Chapter", remote_side=[id])
    sub_chapters = relationship("Chapter", back_populates="parent_chapter")
    articles = relationship("Article", back_populates="chapter", cascade="all, delete-orphan")


class Article(Base):
    """Article d'un document réglementaire"""
    __tablename__ = "regulatory_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    chapter_id = Column(Integer, ForeignKey("regulatory_chapters.id"), nullable=True, index=True)
    document_id = Column(Integer, ForeignKey("regulatory_documents.id"), nullable=False, index=True)
    
    # Informations de l'article
    article_number = Column(String(50), nullable=False, index=True)  # Numéro de l'article
    title = Column(String(500), nullable=True)
    
    # Contenu
    content = Column(Text, nullable=False)  # Contenu de l'article
    
    # Métadonnées
    keywords = Column(JSON, nullable=True)  # Mots-clés spécifiques à l'article
    themes = Column(JSON, nullable=True)  # Thèmes applicables à l'article
    
    # Liens avec d'autres articles
    related_articles = Column(JSON, nullable=True)  # IDs des articles liés
    doc_references = Column(JSON, nullable=True)  # Références à d'autres textes
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    chapter = relationship("Chapter", back_populates="articles")
    document = relationship("RegulatoryDocument")


class Keyword(Base):
    """Mot-clé pour la recherche"""
    __tablename__ = "regulatory_keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    documents = relationship("DocumentKeyword", back_populates="keyword")


class DocumentKeyword(Base):
    """Association document-mot-clé"""
    __tablename__ = "regulatory_document_keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("regulatory_documents.id"), nullable=False, index=True)
    keyword_id = Column(Integer, ForeignKey("regulatory_keywords.id"), nullable=False, index=True)
    
    # Métadonnées
    relevance_score = Column(Float, default=1.0)  # Score de pertinence (0-1)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    document = relationship("RegulatoryDocument", back_populates="keywords")
    keyword = relationship("Keyword", back_populates="documents")


class DocumentTheme(Base):
    """Association document-thème"""
    __tablename__ = "regulatory_document_themes"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("regulatory_documents.id"), nullable=False, index=True)
    theme = Column(String(50), nullable=False, index=True)  # Theme
    
    # Métadonnées
    relevance_score = Column(Float, default=1.0)  # Score de pertinence (0-1)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    document = relationship("RegulatoryDocument", back_populates="themes")


class ArticleLink(Base):
    """Lien entre articles"""
    __tablename__ = "regulatory_article_links"
    
    id = Column(Integer, primary_key=True, index=True)
    source_article_id = Column(Integer, ForeignKey("regulatory_articles.id"), nullable=False, index=True)
    target_article_id = Column(Integer, ForeignKey("regulatory_articles.id"), nullable=False, index=True)
    
    # Type de lien
    link_type = Column(String(50), nullable=False)  # reference, complement, exception, application
    description = Column(Text, nullable=True)
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
