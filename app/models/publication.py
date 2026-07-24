"""
Modèles pour la gestion des publications
Module 5: Publication de l'avis et lancement de la consultation
Relation: 1 commission → plusieurs publications
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from enum import Enum

from app.database import Base


class PublicationType(str, Enum):
    """Types de publications"""
    INITIAL = "initiale"
    MODIFICATION = "modification"
    POSTPONEMENT = "report"
    CANCELLATION = "annulation"
    RECTIFICATION = "rectificatif"


class PublicationStatus(str, Enum):
    """Statuts de publication"""
    DRAFT = "brouillon"
    PENDING = "en_attente"
    PUBLISHED = "publie"
    POSTPONED = "reporte"
    MODIFIED = "modifie"
    CANCELLED = "annule"
    CLOSED = "cloture"


class ProcedureType(str, Enum):
    """Types de procédure"""
    APPEL_OFFRES = "appel_offres"
    CONSULTATION = "consultation"
    MARCHE_SIMPLIFIE = "marche_simplifie"
    GRE_A_PROCEDURE_ADAPTEE = "gre_procedure_adaptee"
    ENTREPRISE_DE_TRAVAUX = "entreprise_travaux"


class SupportType(str, Enum):
    """Types de supports de publication"""
    PORTAIL_MARCHES_PUBLICS = "portail_marches_publics"
    JOURNAL = "journal"
    AFFICHAGE = "affichage"
    SITE_WEB = "site_web"
    AUTRE = "autre"


class Publication(Base):
    """Publication d'avis de marché"""
    __tablename__ = "publications"
    
    id = Column(Integer, primary_key=True, index=True)
    commission_id = Column(Integer, ForeignKey("commissions.id"), nullable=False)
    publication_number = Column(String(50), unique=True, nullable=True)
    
    # Type de publication
    publication_type = Column(SQLEnum(PublicationType), default=PublicationType.INITIAL)
    
    # Informations de publication
    notice_number = Column(String(50), nullable=True)
    object = Column(String(500), nullable=False)
    procedure_type = Column(SQLEnum(ProcedureType), nullable=False)
    contracting_authority = Column(String(200), nullable=True)
    
    # Estimation
    estimated_amount = Column(Float, nullable=True)
    currency = Column(String(10), default="MAD")
    
    # Dates importantes
    publication_date = Column(DateTime, nullable=True)
    submission_deadline = Column(DateTime, nullable=False)
    bid_opening_date = Column(DateTime, nullable=False)
    bid_opening_time = Column(String(10), nullable=True)
    
    # Délai de remise des offres (en jours)
    submission_delay_days = Column(Integer, nullable=True)
    
    # Statut
    status = Column(SQLEnum(PublicationStatus), default=PublicationStatus.DRAFT)
    
    # Observations
    observations = Column(Text, nullable=True)
    
    # Pièces jointes
    attachments = Column(JSON, nullable=True)  # Liste des pièces jointes
    
    # Suppression logique
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    commission = relationship("Commission", back_populates="publications")
    supports = relationship("PublicationSupport", back_populates="publication", cascade="all, delete-orphan")
    deadlines = relationship("PublicationDeadline", back_populates="publication", cascade="all, delete-orphan")
    alerts = relationship("PublicationAlert", back_populates="publication", cascade="all, delete-orphan")
    history = relationship("PublicationHistory", back_populates="publication", cascade="all, delete-orphan")


class PublicationSupport(Base):
    """Support de publication"""
    __tablename__ = "publication_supports"
    
    id = Column(Integer, primary_key=True, index=True)
    publication_id = Column(Integer, ForeignKey("publications.id"), nullable=False)
    
    # Type de support
    support_type = Column(SQLEnum(SupportType), nullable=False)
    
    # Détails du support
    support_name = Column(String(200), nullable=True)  # Nom du journal, URL du site, etc.
    publication_date = Column(DateTime, nullable=True)
    reference = Column(String(100), nullable=True)  # Référence de publication
    
    # Coût
    cost = Column(Float, nullable=True)
    
    # Pièce jointe (preuve de publication)
    attachment_path = Column(String(500), nullable=True)
    attachment_name = Column(String(255), nullable=True)
    
    # Traçabilité
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    publication = relationship("Publication", back_populates="supports")


class PublicationDeadline(Base):
    """Échéance de publication"""
    __tablename__ = "publication_deadlines"
    
    id = Column(Integer, primary_key=True, index=True)
    publication_id = Column(Integer, ForeignKey("publications.id"), nullable=False)
    
    # Type d'échéance
    deadline_type = Column(String(50), nullable=False)  # publication, remise_offres, ouverture_plis, etc.
    
    # Description
    description = Column(String(200), nullable=True)
    
    # Date et heure
    deadline_date = Column(DateTime, nullable=False)
    deadline_time = Column(String(10), nullable=True)
    
    # Statut
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Alertes
    alert_sent = Column(Boolean, default=False)
    alert_sent_at = Column(DateTime, nullable=True)
    
    # Traçabilité
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    publication = relationship("Publication", back_populates="deadlines")


class PublicationAlert(Base):
    """Alerte de publication"""
    __tablename__ = "publication_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    publication_id = Column(Integer, ForeignKey("publications.id"), nullable=False)
    deadline_id = Column(Integer, ForeignKey("publication_deadlines.id"), nullable=True)
    
    # Type d'alerte
    alert_type = Column(String(50), nullable=False)  # deadline_approaching, deadline_missed, missing_info, delay
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    
    # Message
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    
    # Statut
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Traçabilité
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    publication = relationship("Publication", back_populates="alerts")
    deadline = relationship("PublicationDeadline")
    resolver = relationship("User", foreign_keys=[resolved_by])


class PublicationHistory(Base):
    """Historique de publication"""
    __tablename__ = "publication_history"
    
    id = Column(Integer, primary_key=True, index=True)
    publication_id = Column(Integer, ForeignKey("publications.id"), nullable=False)
    
    # Action
    action = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Détails
    status_change = Column(String(50), nullable=True)
    
    # Utilisateur
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_name = Column(String(100), nullable=True)
    
    # Traçabilité
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    publication = relationship("Publication", back_populates="history")
    user = relationship("User")
