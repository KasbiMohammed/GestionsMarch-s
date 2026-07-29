"""
Modèles pour le Chatbot IA métier des marchés publics
Module dédié - Architecture RAG pour l'assistance intelligente
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float,
    ForeignKey, JSON, CheckConstraint, Index
)
from sqlalchemy.orm import relationship

from app.database import Base


# ─────────────────────────────────────────
# Enums métier
# ─────────────────────────────────────────
class MessageType(str, enum.Enum):
    """Types de messages dans la conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class DocumentType(str, enum.Enum):
    """Types de documents indexés"""
    REGLEMENTATION = "reglementation"
    INTERNE = "interne"
    GUIDE = "guide"
    PROCEDURE = "procedure"
    FAQ = "faq"


class QueryType(str, enum.Enum):
    """Types de requêtes"""
    KNOWLEDGE = "knowledge"
    DATABASE = "database"
    ASSISTANCE = "assistance"
    MIXED = "mixed"


# ─────────────────────────────────────────
# Utilitaires
# ─────────────────────────────────────────
def utc_now() -> datetime:
    """Retourne la date/heure UTC actuelle (timezone-aware)."""
    return datetime.now(timezone.utc)


# ─────────────────────────────────────────
# Modèles
# ─────────────────────────────────────────
class ChatSession(Base):
    """Session de conversation avec le chatbot"""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    session_name = Column(String(200), nullable=True)

    # Métadonnées
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )
    is_active = Column(Boolean, default=True, nullable=False)

    # Relations
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at.asc()"
    )
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return (
            f"<ChatSession(id={self.id}, user_id={self.user_id}, "
            f"name='{self.session_name}', active={self.is_active})>"
        )


class ChatMessage(Base):
    """Message dans une conversation"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        Integer,
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    message_type = Column(String(20), nullable=False, index=True)

    # Contenu
    content = Column(Text, nullable=False)

    # Métadonnées de réponse (pour les messages assistant)
    query_type = Column(String(20), nullable=True)
    sources = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    sql_query = Column(Text, nullable=True)

    # Métadonnées
    created_at = Column(
        DateTime, default=utc_now, nullable=False, index=True
    )

    # Relations
    session = relationship("ChatSession", back_populates="messages")
    feedback = relationship(
        "ChatbotFeedback",
        back_populates="message",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        preview = (self.content[:40] + "…") if len(self.content) > 40 else self.content
        return (
            f"<ChatMessage(id={self.id}, session_id={self.session_id}, "
            f"type='{self.message_type}', content='{preview}')>"
        )


class KnowledgeBase(Base):
    """Document dans la base de connaissances (RAG)"""
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    document_type = Column(String(20), nullable=False, index=True)
    title = Column(String(300), nullable=False)

    # Contenu
    content = Column(Text, nullable=False)
    chunk_id = Column(String(100), nullable=True, index=True)
    chunk_index = Column(Integer, nullable=True)

    # Métadonnées
    source = Column(String(200), nullable=True)
    category = Column(String(100), nullable=True, index=True)
    tags = Column(JSON, nullable=True)
    language = Column(String(10), default="fr", nullable=False)

    # Vectorisation (embeddings) — liste de floats stockée en JSON
    # En production, migrer vers pgvector pour la recherche par similarité
    embedding = Column(JSON, nullable=True)

    # Métadonnées
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    created_by = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    def __repr__(self) -> str:
        return (
            f"<KnowledgeBase(id={self.id}, title='{self.title}', "
            f"type='{self.document_type}', active={self.is_active})>"
        )


class DocumentIndex(Base):
    """Index des documents internes de l'application"""
    __tablename__ = "document_index"

    id = Column(Integer, primary_key=True, index=True)

    # Référence au document dans l'application
    document_type = Column(String(50), nullable=False, index=True)
    document_id = Column(Integer, nullable=True, index=True)

    # Contenu indexé
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False)
    doc_metadata = Column(JSON, nullable=True)

    # Vectorisation
    embedding = Column(JSON, nullable=True)

    # Métadonnées
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<DocumentIndex(id={self.id}, doc_type='{self.document_type}', "
            f"doc_id={self.document_id}, title='{self.title}')>"
        )


class ChatbotFeedback(Base):
    """Feedback utilisateur sur les réponses du chatbot"""
    __tablename__ = "chatbot_feedback"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(
        Integer,
        ForeignKey("chat_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Feedback
    rating = Column(Integer, nullable=True)
    is_helpful = Column(Boolean, nullable=True)
    comment = Column(Text, nullable=True)

    # Contrainte métier : rating entre 1 et 5
    __table_args__ = (
        CheckConstraint(
            "rating IS NULL OR (rating >= 1 AND rating <= 5)",
            name="ck_chatbot_feedback_rating_range"
        ),
    )

    # Métadonnées
    created_at = Column(DateTime, default=utc_now, nullable=False)
    created_by = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relations
    message = relationship("ChatMessage", back_populates="feedback")

    def __repr__(self) -> str:
        return (
            f"<ChatbotFeedback(id={self.id}, message_id={self.message_id}, "
            f"rating={self.rating}, helpful={self.is_helpful})>"
        )