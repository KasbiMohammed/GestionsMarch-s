"""
Modèles pour le workflow de validation des dossiers
Module 3: Validation administrative et technique
Relation: 1 préparation → 1 workflow de validation
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from enum import Enum

from app.database import Base


class ValidationStep(str, Enum):
    """Étapes de validation séquentielles"""
    REQUESTING_SERVICE = "service_demandeur"
    TECHNICAL_SERVICE = "service_technique"
    FINANCIAL_SERVICE = "service_financier"
    MARKETS_SERVICE = "service_marches"
    ORDERING_AUTHORITY = "ordonnateur"


class ValidationDecision(str, Enum):
    """Décisions de validation"""
    PENDING = "en_attente"
    VALIDATED = "valide"
    REJECTED = "rejete"
    NEEDS_COMPLETION = "a_completer"


class WorkflowStatus(str, Enum):
    """Statuts du workflow de validation"""
    PENDING = "en_attente_validation"
    IN_PROGRESS = "en_cours_validation"
    NEEDS_COMPLETION = "a_completer"
    VALIDATED = "valide"
    REJECTED = "rejete"


class ValidationWorkflow(Base):
    """Workflow de validation d'un dossier de préparation"""
    __tablename__ = "validation_workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    preparation_id = Column(Integer, ForeignKey("market_preparations.id"), nullable=False, unique=True)
    workflow_number = Column(String(50), unique=True, nullable=True)
    
    # Statut global
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.PENDING)
    current_step = Column(SQLEnum(ValidationStep), default=ValidationStep.REQUESTING_SERVICE)
    
    # Pourcentage de conformité
    conformity_percentage = Column(Integer, default=0)
    
    # Dates
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Observations globales
    global_observations = Column(Text, nullable=True)
    
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
    preparation = relationship("MarketPreparation", back_populates="validation_workflow")
    validations = relationship("ValidationRecord", back_populates="workflow", cascade="all, delete-orphan")
    checklist = relationship("ValidationChecklist", back_populates="workflow", uselist=False, cascade="all, delete-orphan")
    history = relationship("ValidationHistory", back_populates="workflow", cascade="all, delete-orphan")
    alerts = relationship("ValidationAlert", back_populates="workflow", cascade="all, delete-orphan")


class ValidationRecord(Base):
    """Enregistrement d'une validation à une étape"""
    __tablename__ = "validation_records"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("validation_workflows.id"), nullable=False)
    
    # Étape de validation
    step = Column(SQLEnum(ValidationStep), nullable=False)
    
    # Décision
    decision = Column(SQLEnum(ValidationDecision), default=ValidationDecision.PENDING)
    
    # Validateur
    validator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    validator_name = Column(String(200), nullable=True)
    validator_role = Column(String(100), nullable=True)
    
    # Dates
    validated_at = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)
    
    # Observations et commentaires
    observations = Column(Text, nullable=True)
    comments = Column(Text, nullable=True)
    
    # Pièces jointes de validation
    attachment_path = Column(String(500), nullable=True)
    attachment_name = Column(String(255), nullable=True)
    
    # Si rejet ou demande de complément
    return_step = Column(SQLEnum(ValidationStep), nullable=True)
    return_reason = Column(Text, nullable=True)
    
    # Traçabilité
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    workflow = relationship("ValidationWorkflow", back_populates="validations")
    validator = relationship("User", foreign_keys=[validator_id])


class ValidationChecklist(Base):
    """Checklist de conformité du dossier"""
    __tablename__ = "validation_checklists"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("validation_workflows.id"), nullable=False, unique=True)
    
    # Critères de conformité
    documents_complete = Column(Boolean, default=False)
    documents_observations = Column(Text, nullable=True)
    
    budget_valid = Column(Boolean, default=False)
    budget_observations = Column(Text, nullable=True)
    
    estimates_valid = Column(Boolean, default=False)
    estimates_observations = Column(Text, nullable=True)
    
    signatures_valid = Column(Boolean, default=False)
    signatures_observations = Column(Text, nullable=True)
    
    information_coherent = Column(Boolean, default=False)
    information_observations = Column(Text, nullable=True)
    
    regulatory_compliance = Column(Boolean, default=False)
    regulatory_observations = Column(Text, nullable=True)
    
    # Critères supplémentaires (JSON flexible)
    additional_criteria = Column(JSON, nullable=True)
    
    # Pourcentage calculé
    calculated_percentage = Column(Integer, default=0)
    
    # Traçabilité
    checked_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    checked_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    workflow = relationship("ValidationWorkflow", back_populates="checklist")
    checker = relationship("User", foreign_keys=[checked_by])


class ValidationHistory(Base):
    """Historique complet des validations"""
    __tablename__ = "validation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("validation_workflows.id"), nullable=False)
    
    # Action
    action = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Détails de l'action
    from_step = Column(SQLEnum(ValidationStep), nullable=True)
    to_step = Column(SQLEnum(ValidationStep), nullable=True)
    decision = Column(SQLEnum(ValidationDecision), nullable=True)
    
    # Utilisateur
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_name = Column(String(100), nullable=True)
    user_role = Column(String(100), nullable=True)
    
    # Traçabilité
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    workflow = relationship("ValidationWorkflow", back_populates="history")
    user = relationship("User")


class ValidationAlert(Base):
    """Alertes pour le workflow de validation"""
    __tablename__ = "validation_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("validation_workflows.id"), nullable=False)
    
    # Type d'alerte
    alert_type = Column(String(50), nullable=False)  # pending_validation, overdue_validation, needs_completion, rejected
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    
    # Message
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    
    # Étape concernée
    step = Column(SQLEnum(ValidationStep), nullable=True)
    
    # Statut
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Traçabilité
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    workflow = relationship("ValidationWorkflow", back_populates="alerts")
