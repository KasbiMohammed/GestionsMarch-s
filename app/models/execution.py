"""
Modèles pour l'exécution des marchés
Module 9: Exécution du marché
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from enum import Enum

from app.database import Base


class ExecutionStatus(str, Enum):
    """Statuts d'exécution"""
    NOT_STARTED = "non_commencé"
    IN_PROGRESS = "en_cours"
    SUSPENDED = "suspendu"
    COMPLETED = "terminé"
    CANCELLED = "annulé"


class ServiceOrder(Base):
    """Ordre de service"""
    __tablename__ = "service_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    
    # Informations
    order_number = Column(String(50), nullable=False)
    order_type = Column(String(50), nullable=False)  # démarrage, reprise, suspension, arrêt
    order_date = Column(DateTime, nullable=False)
    
    # Description
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    
    # Date d'effet
    effective_date = Column(DateTime, nullable=True)
    
    # Validation
    validated = Column(Boolean, default=False)
    validated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    
    # Notification
    notified = Column(Boolean, default=False)
    notified_at = Column(DateTime, nullable=True)
    
    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    market = relationship("Market", back_populates="service_orders")


class ExecutionPlan(Base):
    """Planning d'exécution"""
    __tablename__ = "execution_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    
    # Planning
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    total_duration = Column(Integer, nullable=False)  # en jours
    
    # Phases
    phases = Column(JSON, nullable=True)  # Liste des phases avec dates
    
    # Statut
    status = Column(SQLEnum(ExecutionStatus), default=ExecutionStatus.NOT_STARTED)
    
    # Progression
    progress_percentage = Column(Float, default=0.0)
    
    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    market = relationship("Market", back_populates="execution_plan")
    milestones = relationship("Milestone", back_populates="execution_plan", cascade="all, delete-orphan")


class Milestone(Base):
    """Jalon d'exécution"""
    __tablename__ = "milestones"
    
    id = Column(Integer, primary_key=True, index=True)
    execution_plan_id = Column(Integer, ForeignKey("execution_plans.id"), nullable=False)
    
    # Informations
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    planned_date = Column(DateTime, nullable=False)
    actual_date = Column(DateTime, nullable=True)
    
    # Statut
    completed = Column(Boolean, default=False)
    on_time = Column(Boolean, nullable=True)
    
    # Traçabilité
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    execution_plan = relationship("ExecutionPlan", back_populates="milestones")


class Attachment(Base):
    """Attachement (constat d'avancement)"""
    __tablename__ = "attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    
    # Informations
    attachment_number = Column(String(50), nullable=False)
    attachment_date = Column(DateTime, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Progression
    work_percentage = Column(Float, nullable=False)
    
    # Montant
    amount = Column(Float, nullable=False)
    
    # Validation
    validated = Column(Boolean, default=False)
    validated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    
    # Observations
    observations = Column(Text, nullable=True)
    
    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    market = relationship("Market", back_populates="attachments")


class Payment(Base):
    """Paiement / Décompte"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    attachment_id = Column(Integer, ForeignKey("attachments.id"), nullable=True)
    
    # Type de paiement
    payment_type = Column(String(50), nullable=False)  # acompte, situation, solde, retenue
    payment_number = Column(String(50), nullable=False)
    
    # Montant
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="MAD")
    
    # Dates
    payment_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=True)
    
    # Statut
    paid = Column(Boolean, default=False)
    paid_at = Column(DateTime, nullable=True)
    payment_reference = Column(String(100), nullable=True)
    
    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    market = relationship("Market", back_populates="payments")
    attachment = relationship("Attachment")


class Amendment(Base):
    """Avenant"""
    __tablename__ = "amendments"
    
    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    
    # Informations
    amendment_number = Column(String(50), nullable=False)
    amendment_date = Column(DateTime, nullable=False)
    
    # Type d'avenant
    amendment_type = Column(String(50), nullable=False)  # prolongation, augmentation, réduction, modification
    
    # Modifications
    original_amount = Column(Float, nullable=True)
    new_amount = Column(Float, nullable=True)
    amount_difference = Column(Float, nullable=True)
    
    original_duration = Column(Integer, nullable=True)  # en jours
    new_duration = Column(Integer, nullable=True)  # en jours
    duration_difference = Column(Integer, nullable=True)  # en jours
    
    # Justification
    justification = Column(Text, nullable=True)
    
    # Validation
    validated = Column(Boolean, default=False)
    validated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    
    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    market = relationship("Market", back_populates="amendments")


class Guarantee(Base):
    """Garantie / Caution"""
    __tablename__ = "guarantees"
    
    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    
    # Type de garantie
    guarantee_type = Column(String(50), nullable=False)  # provisoire, définitive, retenue, bonne_fin
    guarantee_number = Column(String(100), nullable=False)
    
    # Banque
    bank_name = Column(String(200), nullable=False)
    bank_reference = Column(String(100), nullable=True)
    
    # Montant
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="MAD")
    
    # Dates
    issue_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    
    # Statut
    active = Column(Boolean, default=True)
    released = Column(Boolean, default=False)
    released_at = Column(DateTime, nullable=True)
    released_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Fichier
    document_path = Column(String(500), nullable=True)
    
    # Alertes
    expiry_alert_sent = Column(Boolean, default=False)
    
    # Traçabilité
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    market = relationship("Market", back_populates="guarantees")


class Penalty(Base):
    """Pénalité"""
    __tablename__ = "penalties"
    
    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    
    # Type de pénalité
    penalty_type = Column(String(50), nullable=False)  # retard, qualité, non_conformité
    penalty_reference = Column(String(100), nullable=False)
    
    # Montant
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="MAD")
    
    # Justification
    reason = Column(Text, nullable=False)
    
    # Dates
    penalty_date = Column(DateTime, nullable=False)
    
    # Statut
    applied = Column(Boolean, default=False)
    applied_at = Column(DateTime, nullable=True)
    paid = Column(Boolean, default=False)
    paid_at = Column(DateTime, nullable=True)
    
    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    market = relationship("Market", back_populates="penalties")


class Reception(Base):
    """Réception (provisoire ou définitive)"""
    __tablename__ = "receptions"
    
    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    
    # Type de réception
    reception_type = Column(String(50), nullable=False)  # provisoire, définitive
    reception_number = Column(String(50), nullable=False)
    reception_date = Column(DateTime, nullable=False)
    
    # Réserves
    has_reserves = Column(Boolean, default=False)
    reserves = Column(Text, nullable=True)
    
    # Levée des réserves
    reserves_lifted = Column(Boolean, default=False)
    reserves_lifted_date = Column(DateTime, nullable=True)
    
    # PV
    pv_reference = Column(String(100), nullable=True)
    pv_date = Column(DateTime, nullable=True)
    
    # Validation
    validated = Column(Boolean, default=False)
    validated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    
    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    market = relationship("Market", back_populates="receptions")
