"""
Modèles pour la planification des marchés publics
Module: Planification des Marchés
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime,
    ForeignKey, Enum as SQLEnum,
)
from sqlalchemy.orm import relationship

from app.database import Base


class ProjectType(str, Enum):
    """Type de projet"""
    TRAVAUX = "travaux"
    FOURNITURES = "fournitures"
    SERVICES = "services"
    PRESTATIONS_INTELLECTUELLES = "prestations_intellectuelles"


class ProcedureType(str, Enum):
    """Type de procédure de passation"""
    BON_COMMANDE = "bon_commande"
    MARCHE_SIMPLIFIE = "marche_simplifie"
    AO_OUVERT = "ao_ouvert"
    AO_RESTREINT = "ao_restreint"
    CONSULTATION = "consultation"
    PROCEDURE_NEGOCIEE = "procedure_negociee"


class PlanningPriority(str, Enum):
    """Priorité de la planification"""
    FAIBLE = "faible"
    MOYENNE = "moyenne"
    HAUTE = "haute"
    URGENTE = "urgente"


class MarketPlanningStatus(str, Enum):
    """Statut de la planification"""
    BROUILLON = "brouillon"
    EN_PREPARATION = "en_preparation"
    VALIDEE = "validee"
    PROGRAMMEE = "programmee"
    ANNULEE = "annulee"


class MarketPlanning(Base):
    """Planification d'un marché public"""
    __tablename__ = "market_plannings"
    markets = relationship(
        "Market",
        back_populates="planning",
        foreign_keys="Market.planning_id"
    )
    id = Column(Integer, primary_key=True, index=True)
    planning_number = Column(String(50), unique=True, nullable=False, index=True)
    fiscal_year = Column(Integer, nullable=False, index=True)

    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)

    project_type = Column(SQLEnum(ProjectType), nullable=False)
    procedure_type = Column(SQLEnum(ProcedureType), nullable=False)

    estimated_budget = Column(Float, nullable=False, default=0.0)
    funding_source = Column(String(200), nullable=True)
    
    # Maître d'ouvrage
    master_of_work = Column(String(200), nullable=True, default="Commune")

    requesting_service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    requesting_service_name = Column(String(200), nullable=True)
    responsible_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    responsible_name = Column(String(200), nullable=True)

    priority = Column(SQLEnum(PlanningPriority), default=PlanningPriority.MOYENNE)
    status = Column(SQLEnum(MarketPlanningStatus), default=MarketPlanningStatus.BROUILLON)
    
    # Progression de la planification
    progress_percentage = Column(Integer, default=0)

    # Dates prévisionnelles
    launch_date = Column(DateTime, nullable=True)
    bid_opening_date = Column(DateTime, nullable=True)
    attribution_date = Column(DateTime, nullable=True)
    notification_date = Column(DateTime, nullable=True)
    service_order_date = Column(DateTime, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    observations = Column(Text, nullable=True)

    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    modified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    requesting_service = relationship("Service", foreign_keys=[requesting_service_id])
    responsible = relationship("User", foreign_keys=[responsible_id])
    creator = relationship("User", foreign_keys=[created_by])
    documents = relationship(
        "PlanningDocument",
        back_populates="planning",
        cascade="all, delete-orphan",
    )
    preparation = relationship("MarketPreparation", back_populates="planning", uselist=False, cascade="all, delete-orphan")
    market = relationship("Market", back_populates="planning", uselist=False)

    def __repr__(self):
        return f"<MarketPlanning(id={self.id}, number='{self.planning_number}')>"


class PlanningDocument(Base):
    """Document joint à une planification"""
    __tablename__ = "planning_documents"

    id = Column(Integer, primary_key=True, index=True)
    planning_id = Column(Integer, ForeignKey("market_plannings.id"), nullable=False)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Float, nullable=True)
    file_type = Column(String(100), nullable=True)

    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    planning = relationship("MarketPlanning", back_populates="documents")

    def __repr__(self):
        return f"<PlanningDocument(id={self.id}, name='{self.name}')>"
