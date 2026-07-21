"""
Modèles pour la préparation des marchés
Module 2: Préparation du marché
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from enum import Enum

from app.database import Base


class PreparationStatus(str, Enum):
    """Statuts de la préparation"""
    DRAFT = "brouillon"
    IN_PROGRESS = "en_cours"
    TECHNICAL_VALIDATION = "validation_technique"
    FINANCIAL_VALIDATION = "validation_financière"
    JURIDICAL_VALIDATION = "validation_juridique"
    INTERNAL_VISA = "visa_interne"
    READY = "prêt"
    PUBLISHED = "publié"


class MarketPreparation(Base):
    """Préparation d'un marché"""
    __tablename__ = "market_preparations"
    
    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    need_id = Column(Integer, ForeignKey("service_needs.id"), nullable=True)
    
    # Définition du besoin
    need_description = Column(Text, nullable=False)
    technical_specifications = Column(Text, nullable=True)
    performance_requirements = Column(Text, nullable=True)
    
    # Estimation des coûts
    estimated_amount = Column(Float, nullable=False)
    cost_breakdown = Column(JSON, nullable=True)  # Détail des coûts
    
    # Choix du mode de passation
    procurement_method = Column(String(100), nullable=False)
    procurement_justification = Column(Text, nullable=True)
    
    # Statut de préparation
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
    
    juridical_validation = Column(Boolean, default=False)
    juridical_validator = Column(Integer, ForeignKey("users.id"), nullable=True)
    juridical_validation_date = Column(DateTime, nullable=True)
    juridical_validation_comments = Column(Text, nullable=True)
    
    internal_visa = Column(Boolean, default=False)
    visa_signer = Column(Integer, ForeignKey("users.id"), nullable=True)
    visa_date = Column(DateTime, nullable=True)
    
    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    market = relationship("Market", back_populates="preparation")
    need = relationship("ServiceNeed")
    cps = relationship("CPS", back_populates="preparation", uselist=False, cascade="all, delete-orphan")
    bpu = relationship("BPU", back_populates="preparation", uselist=False, cascade="all, delete-orphan")
    dqe = relationship("DQE", back_populates="preparation", uselist=False, cascade="all, delete-orphan")


class CPS(Base):
    """Cahier des Prescriptions Spéciales"""
    __tablename__ = "cps"
    
    id = Column(Integer, primary_key=True, index=True)
    preparation_id = Column(Integer, ForeignKey("market_preparations.id"), nullable=False)
    
    # Contenu du CPS
    general_conditions = Column(Text, nullable=True)
    special_conditions = Column(Text, nullable=True)
    technical_specifications = Column(Text, nullable=True)
    administrative_clauses = Column(Text, nullable=True)
    financial_clauses = Column(Text, nullable=True)
    legal_clauses = Column(Text, nullable=True)
    
    # Références réglementaires
    regulatory_references = Column(Text, nullable=True)
    
    # Validation
    validated = Column(Boolean, default=False)
    validated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    
    # Version
    version = Column(Integer, default=1)
    
    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    preparation = relationship("MarketPreparation", back_populates="cps")


class BPU(Base):
    """Bordereau des Prix Unitaires"""
    __tablename__ = "bpu"
    
    id = Column(Integer, primary_key=True, index=True)
    preparation_id = Column(Integer, ForeignKey("market_preparations.id"), nullable=False)
    
    # Structure du BPU
    items = Column(JSON, nullable=True)  # Liste des articles avec prix unitaires
    
    # Validation
    validated = Column(Boolean, default=False)
    validated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    
    # Version
    version = Column(Integer, default=1)
    
    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    preparation = relationship("MarketPreparation", back_populates="bpu")


class DQE(Base):
    """Devis Quantitatif Estimatif"""
    __tablename__ = "dqe"
    
    id = Column(Integer, primary_key=True, index=True)
    preparation_id = Column(Integer, ForeignKey("market_preparations.id"), nullable=False)
    
    # Structure du DQE
    chapters = Column(JSON, nullable=True)  # Chapitres et quantités estimées
    
    # Validation
    validated = Column(Boolean, default=False)
    validated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    
    # Version
    version = Column(Integer, default=1)
    
    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    preparation = relationship("MarketPreparation", back_populates="dqe")


class TechnicalPlan(Base):
    """Plans et études techniques"""
    __tablename__ = "technical_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    preparation_id = Column(Integer, ForeignKey("market_preparations.id"), nullable=False)
    
    # Informations du plan
    reference = Column(String(100), nullable=False)
    description = Column(String(200), nullable=True)
    plan_type = Column(String(50), nullable=True)  # architectural, structural, electrical, etc.
    
    # Fichier
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    
    # Validation
    validated = Column(Boolean, default=False)
    validated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    
    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
