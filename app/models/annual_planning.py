"""
Modèles pour la planification annuelle des achats
Module 1: Planification annuelle des achats
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum

from app.database import Base


class PlanningStatus(str, Enum):
    """Statuts de la planification"""
    DRAFT = "brouillon"
    SUBMITTED = "soumis"
    VALIDATED = "validé"
    APPROVED = "approuvé"
    REJECTED = "rejeté"


class NeedPriority(str, Enum):
    """Priorité des besoins"""
    LOW = "faible"
    MEDIUM = "moyenne"
    HIGH = "haute"
    URGENT = "urgent"


class AnnualPlanning(Base):
    """Programme prévisionnel annuel"""
    __tablename__ = "annual_plannings"
    
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    
    # Informations générales
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Budget
    total_budget = Column(Float, default=0.0)
    allocated_budget = Column(Float, default=0.0)
    consumed_budget = Column(Float, default=0.0)
    remaining_budget = Column(Float, default=0.0)
    
    # Statut et validation
    status = Column(SQLEnum(PlanningStatus), default=PlanningStatus.DRAFT)
    submitted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    validated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Observations
    observations = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    needs = relationship("ServiceNeed", back_populates="planning", cascade="all, delete-orphan")
    service = relationship("Service", back_populates="plannings")
    submitter = relationship("User", foreign_keys=[submitted_by])
    validator = relationship("User", foreign_keys=[validated_by])
    approver = relationship("User", foreign_keys=[approved_by])


class ServiceNeed(Base):
    """Besoin de service pour un marché"""
    __tablename__ = "service_needs"
    
    id = Column(Integer, primary_key=True, index=True)
    planning_id = Column(Integer, ForeignKey("annual_plannings.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    
    # Description du besoin
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(SQLEnum(NeedPriority), default=NeedPriority.MEDIUM)
    
    # Estimation
    estimated_amount = Column(Float, nullable=False)
    estimated_duration = Column(Integer, nullable=True)  # en jours
    currency = Column(String(10), default="MAD")
    
    # Type de marché
    market_type = Column(String(50), nullable=True)
    market_nature = Column(String(50), nullable=True)  # travaux, fournitures, services
    
    # Calendrier prévisionnel
    planned_start_date = Column(DateTime, nullable=True)
    planned_end_date = Column(DateTime, nullable=True)
    planned_publication_date = Column(DateTime, nullable=True)
    
    # Budget
    budget_code = Column(String(50), nullable=True)
    credit_line = Column(String(100), nullable=True)
    
    # Statut
    is_realized = Column(Boolean, default=False)
    realized_market_id = Column(Integer, ForeignKey("markets.id"), nullable=True)
    
    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    planning = relationship("AnnualPlanning", back_populates="needs")
    service = relationship("Service", back_populates="needs")
    realized_market = relationship("Market", back_populates="service_need")
    estimates = relationship("BudgetEstimate", back_populates="need", cascade="all, delete-orphan")


class BudgetEstimate(Base):
    """Estimation budgétaire détaillée"""
    __tablename__ = "budget_estimates"
    
    id = Column(Integer, primary_key=True, index=True)
    need_id = Column(Integer, ForeignKey("service_needs.id"), nullable=False)
    
    # Détails de l'estimation
    category = Column(String(100), nullable=False)
    description = Column(String(200), nullable=True)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    
    # Justification
    justification = Column(Text, nullable=True)
    reference = Column(String(100), nullable=True)  # Référence à un marché similaire
    
    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    need = relationship("ServiceNeed", back_populates="estimates")


class Service(Base):
    """Service de la commune"""
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    director_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    budget_code = Column(String(50), nullable=True)
    
    # Relations
    needs = relationship("ServiceNeed", back_populates="service")
    plannings = relationship("AnnualPlanning", back_populates="service")
    director = relationship("User", foreign_keys=[director_id])
