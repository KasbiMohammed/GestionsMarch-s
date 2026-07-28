"""
Modèles pour le Chatbot IA métier des marchés publics
Module dédié - Architecture RAG pour l'assistance intelligente
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from enum import Enum
import enum

from app.database import Base


class MessageType(str, enum.Enum):
    """Types de messages dans la conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class DocumentType(str, enum.Enum):
    """Types de documents indexés"""
    REGLEMENTATION = "reglementation"  # Décret 2-22-431, CCAG, guides
    INTERNE = "interne"  # CPS, RC, BPU, DQE, PV, contrats
    GUIDE = "guide"  # Guides PMMP, circulaires
    PROCEDURE = "procedure"  # Procédures internes
    FAQ = "faq"  # Questions fréquentes


class QueryType(str, enum.Enum):
    """Types de requêtes"""
    KNOWLEDGE = "knowledge"  # Recherche dans la base de connaissances
    DATABASE = "database"  # Interrogation de la base de données
    ASSISTANCE = "assistance"  # Assistance sur l'utilisation de l'application
    MIXED = "mixed"  # Combinaison de plusieurs sources


class ChatSession(Base):
    """Session de conversation avec le chatbot"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_name = Column(String(200), nullable=True)  # Nom optionnel de la session
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relations
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    user = relationship("User", foreign_keys=[user_id])


class ChatMessage(Base):
    """Message dans une conversation"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    message_type = Column(String(20), nullable=False)  # user, assistant, system
    
    # Contenu
    content = Column(Text, nullable=False)
    
    # Métadonnées de réponse (pour les messages assistant)
    query_type = Column(String(20), nullable=True)  # knowledge, database, assistance, mixed
    sources = Column(JSON, nullable=True)  # Sources utilisées pour la réponse
    confidence = Column(Float, nullable=True)  # Score de confiance de la réponse
    sql_query = Column(Text, nullable=True)  # Requête SQL générée (si applicable)
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    session = relationship("ChatSession", back_populates="messages")


class KnowledgeBase(Base):
    """Document dans la base de connaissances (RAG)"""
    __tablename__ = "knowledge_base"
    
    id = Column(Integer, primary_key=True, index=True)
    document_type = Column(String(20), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    
    # Contenu
    content = Column(Text, nullable=False)  # Texte complet du document
    chunk_id = Column(String(100), nullable=True, index=True)  # ID du chunk (pour documents découpés)
    chunk_index = Column(Integer, nullable=True)  # Index du chunk dans le document
    
    # Métadonnées
    source = Column(String(200), nullable=True)  # Source du document (ex: "Décret 2-22-431")
    category = Column(String(100), nullable=True, index=True)  # Catégorie (ex: "Publication", "Exécution")
    tags = Column(JSON, nullable=True)  # Tags pour la recherche
    language = Column(String(10), default="fr")
    
    # Vectorisation (embeddings)
    embedding = Column(JSON, nullable=True)  # Vecteur d'embedding
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Indexation
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)


class DocumentIndex(Base):
    """Index des documents internes de l'application"""
    __tablename__ = "document_index"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Référence au document dans l'application
    document_type = Column(String(50), nullable=False)  # market, planning, stage, document
    document_id = Column(Integer, nullable=True)  # ID du document dans l'application
    
    # Contenu indexé
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False)
    doc_metadata = Column(JSON, nullable=True)  # Métadonnées supplémentaires
    
    # Vectorisation
    embedding = Column(JSON, nullable=True)
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class ChatbotFeedback(Base):
    """Feedback utilisateur sur les réponses du chatbot"""
    __tablename__ = "chatbot_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=False, index=True)
    
    # Feedback
    rating = Column(Integer, nullable=True)  # 1-5 étoiles
    is_helpful = Column(Boolean, nullable=True)
    comment = Column(Text, nullable=True)
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
