"""
Modèles pour le workflow complet
Module 15: Workflow complet
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey,Float, Boolean, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from enum import Enum

from app.database import Base


class WorkflowStep(str, Enum):
    """Étapes du workflow"""
    PLANNING = "planification"
    BUDGET_VALIDATION = "validation_budgétaire"
    TECHNICAL_STUDIES = "études_techniques"
    DCE_PREPARATION = "préparation_dce"
    VALIDATION = "validation"
    PMMP_PUBLICATION = "publication_pmmp"
    OFFER_RECEPTION = "réception_offres"
    BID_OPENING = "ouverture_plis"
    ANALYSIS = "analyse"
    RANKING = "classement"
    COMMISSION = "commission"
    ATTRIBUTION = "attribution"
    NOTIFICATION = "notification"
    SERVICE_ORDER = "ordre_service"
    EXECUTION = "exécution"
    PAYMENTS = "paiements"
    PROVISIONAL_RECEPTION = "réception_provisoire"
    RESERVE_LIFTING = "levée_réserves"
    DEFINITIVE_RECEPTION = "réception_définitive"
    ARCHIVING = "archivage"


class WorkflowStatus(str, Enum):
    """Statuts du workflow"""
    PENDING = "en_attente"
    IN_PROGRESS = "en_cours"
    COMPLETED = "terminé"
    SKIPPED = "sauté"
    FAILED = "échoué"


class Workflow(Base):
    """Workflow d'un marché"""
    __tablename__ = "workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    
    # Informations
    workflow_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Statut global
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.PENDING)
    
    # Progression
    current_step = Column(SQLEnum(WorkflowStep), nullable=True)
    progress_percentage = Column(Float, default=0.0)
    
    # Dates
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    market = relationship("Market", back_populates="workflow")
    steps = relationship("WorkflowStepExecution", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowStepExecution(Base):
    """Exécution d'une étape du workflow"""
    __tablename__ = "workflow_step_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    
    # Étape
    step = Column(SQLEnum(WorkflowStep), nullable=False)
    step_order = Column(Integer, nullable=False)
    
    # Statut
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.PENDING)
    
    # Responsables
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Dates
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    planned_duration = Column(Integer, nullable=True)  # en jours
    actual_duration = Column(Integer, nullable=True)  # en jours
    
    # Résultat
    result = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Documents
    documents = Column(JSON, nullable=True)  # Liste des documents générés
    
    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    workflow = relationship("Workflow", back_populates="steps")
    assigned_user = relationship("User", foreign_keys=[assigned_to])


class WorkflowTransition(Base):
    """Transition entre étapes du workflow"""
    __tablename__ = "workflow_transitions"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    
    # Transition
    from_step = Column(SQLEnum(WorkflowStep), nullable=True)
    to_step = Column(SQLEnum(WorkflowStep), nullable=False)
    
    # Conditions
    conditions = Column(JSON, nullable=True)
    
    # Validation
    validated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    
    # Observations
    observations = Column(Text, nullable=True)
    
    # Traçabilité
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    workflow = relationship("Workflow")
