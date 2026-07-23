"""
Modèles pour la préparation des marchés
Module 2: Préparation du dossier du marché
Relation: 1 planification → 1 dossier de préparation
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from enum import Enum

from app.database import Base


class PreparationStatus(str, Enum):
    """Statuts de la préparation"""
    DRAFT = "en_preparation"
    IN_PROGRESS = "en_cours"
    PENDING_VALIDATION = "en_attente_validation"
    VALIDATED = "valide"
    REJECTED = "rejete"


class MarketPreparation(Base):
    """Préparation d'un marché - Dossier de préparation"""
    __tablename__ = "market_preparations"
    
    id = Column(Integer, primary_key=True, index=True)
    planning_id = Column(Integer, ForeignKey("market_plannings.id"), nullable=False, unique=True)
    
    # Informations générales
    preparation_number = Column(String(50), unique=True, nullable=True)
    object = Column(String(300), nullable=False)
    procurement_type = Column(String(50), nullable=True)
    procedure_type = Column(String(50), nullable=True)
    requesting_service = Column(String(200), nullable=True)
    responsible_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    duration = Column(Integer, nullable=True)  # en jours
    location = Column(String(200), nullable=True)
    
    # Budget et financement
    estimated_budget = Column(Float, nullable=False)
    funding_source = Column(String(200), nullable=True)
    
    # Progression et statut
    progress_percentage = Column(Integer, default=0)
    status = Column(SQLEnum(PreparationStatus), default=PreparationStatus.DRAFT)
    
    # Validations
    technical_validation = Column(Boolean, default=False)
    technical_validator = Column(Integer, ForeignKey("users.id"), nullable=True)
    technical_validation_date = Column(DateTime, nullable=True)
    technical_validation_comments = Column(Text, nullable=True)
    
    financial_validation = Column(Boolean, default=False)
    financial_validator = Column(Integer, ForeignKey("users.id"), nullable=True)
    financial_validation_date = Column(DateTime, nullable=True)
    financial_validation_comments = Column(Text, nullable=True)
    
    administrative_validation = Column(Boolean, default=False)
    administrative_validator = Column(Integer, ForeignKey("users.id"), nullable=True)
    administrative_validation_date = Column(DateTime, nullable=True)
    administrative_validation_comments = Column(Text, nullable=True)
    
    # Observations
    observations = Column(Text, nullable=True)
    
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
    planning = relationship("MarketPlanning", back_populates="preparation")
    responsible = relationship("User", foreign_keys=[responsible_id])
    documents = relationship("PreparationDocument", back_populates="preparation", cascade="all, delete-orphan")
    history = relationship("PreparationHistory", back_populates="preparation", cascade="all, delete-orphan")
    alerts = relationship("PreparationAlert", back_populates="preparation", cascade="all, delete-orphan")
    validation_workflow = relationship("ValidationWorkflow", back_populates="preparation", uselist=False, cascade="all, delete-orphan")


class PreparationDocument(Base):
    """Documents préparatoires du dossier de préparation"""
    __tablename__ = "preparation_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    preparation_id = Column(Integer, ForeignKey("market_preparations.id"), nullable=False)
    
    # Type de document
    document_type = Column(String(50), nullable=False)  # CPS, RC, AE, BPU, DQE, estimation, plans, etc.
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Fichier
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)
    file_type = Column(String(50), nullable=True)
    
    # Statut
    is_required = Column(Boolean, default=True)
    is_uploaded = Column(Boolean, default=False)
    validated = Column(Boolean, default=False)
    validated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    
    # Traçabilité
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    preparation = relationship("MarketPreparation", back_populates="documents")


class PreparationHistory(Base):
    """Historique des actions sur le dossier de préparation"""
    __tablename__ = "preparation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    preparation_id = Column(Integer, ForeignKey("market_preparations.id"), nullable=False)
    
    # Action
    action = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Utilisateur
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_name = Column(String(100), nullable=True)
    
    # Traçabilité
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    preparation = relationship("MarketPreparation", back_populates="history")
    user = relationship("User")


class PreparationAlert(Base):
    """Alertes pour le dossier de préparation"""
    __tablename__ = "preparation_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    preparation_id = Column(Integer, ForeignKey("market_preparations.id"), nullable=False)
    
    # Type d'alerte
    alert_type = Column(String(50), nullable=False)  # missing_documents, pending_validation, delay, open_observations
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
    preparation = relationship("MarketPreparation", back_populates="alerts")
