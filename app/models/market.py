"""
Modèles pour la gestion des marchés publics et des entreprises
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class MarketType(str, enum.Enum):
    """Types de marchés"""
    TRAVAUX = "travaux"
    FOURNITURES = "fournitures"
    SERVICES = "services"
    ETUDES = "etudes"


class ProcurementMethod(str, enum.Enum):
    """Modes de passation"""
    APPEL_OFFRES_OUVERT = "appel_offres_ouvert"
    APPEL_OFFRES_RESTREINT = "appel_offres_restreint"
    MARCHE_NEGOCIE = "marche_negocie"
    BON_COMMANDE = "bon_commande"
    MARCHE_SIMPLIFIE = "marche_simplifie"
    CONSULTATION = "consultation"


class MarketStatus(str, enum.Enum):
    """Statuts des marchés"""
    PLANIFIE = "planifie"
    EN_COURS = "en_cours"
    TERMINE = "termine"
    EN_ATTENTE = "en_attente"
    EN_RETARD = "en_retard"
    ANNULE = "annule"
    SUSPENDU = "suspendu"


class Market(Base):
    """Modèle Marché Public"""
    __tablename__ = "markets"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Informations générales
    market_number = Column(String(50), unique=True, index=True, nullable=False)
    object = Column(Text, nullable=False)
    master_of_work = Column(String(200), nullable=False)  # Maître d'ouvrage
    market_type = Column(Enum(MarketType), nullable=False)
    procurement_method = Column(Enum(ProcurementMethod), nullable=False)
    
    # Budget et montants
    estimated_amount = Column(Float, nullable=False)
    definitive_amount = Column(Float)
    budget = Column(Float)
    credits = Column(Float)
    
    # Services et responsables
    responsible_service = Column(String(200))
    follow_up_responsible = Column(String(200))
    
    # Dates importantes
    publication_date = Column(DateTime)
    opening_date = Column(DateTime)
    attribution_date = Column(DateTime)
    notification_date = Column(DateTime)
    start_date = Column(DateTime)
    provisional_acceptance_date = Column(DateTime)
    definitive_acceptance_date = Column(DateTime)
    expected_end_date = Column(DateTime)
    actual_end_date = Column(DateTime)
    
    # Statut et progression
    status = Column(Enum(MarketStatus), default=MarketStatus.PLANIFIE)
    progress_percentage = Column(Integer, default=0)
    
    # Entreprises
    participating_companies_count = Column(Integer, default=0)
    
    # Observations
    observations = Column(Text)
    comments = Column(Text)
    
    # Audit
    created_by = Column(Integer, ForeignKey("users.id"))
    modified_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relations
    created_by_user = relationship("User", foreign_keys=[created_by], back_populates="created_markets")
    modified_by_user = relationship("User", foreign_keys=[modified_by], back_populates="modified_markets")
    companies = relationship("Company", back_populates="market", cascade="all, delete-orphan")
    stages = relationship("Stage", back_populates="market", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="market", cascade="all, delete-orphan")
    histories = relationship("History", back_populates="market", cascade="all, delete-orphan")
    service_need = relationship("ServiceNeed", back_populates="realized_market", uselist=False)

    # Relations ajoutées (manquaient et provoquaient des erreurs de mapping SQLAlchemy)
    alerts = relationship("Alert", back_populates="market", cascade="all, delete-orphan")
    attribution = relationship("Attribution", back_populates="market", uselist=False, cascade="all, delete-orphan")
    # Commission is related to ValidationWorkflow, not directly to Market
    service_orders = relationship("ServiceOrder", back_populates="market", cascade="all, delete-orphan")
    execution_plan = relationship("ExecutionPlan", back_populates="market", uselist=False, cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="market", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="market", cascade="all, delete-orphan")
    amendments = relationship("Amendment", back_populates="market", cascade="all, delete-orphan")
    guarantees = relationship("Guarantee", back_populates="market", cascade="all, delete-orphan")
    penalties = relationship("Penalty", back_populates="market", cascade="all, delete-orphan")
    receptions = relationship("Reception", back_populates="market", cascade="all, delete-orphan")
    preparation = relationship("MarketPreparation", back_populates="market", uselist=False, cascade="all, delete-orphan")
    pmmp_publication = relationship("PMMPPublication", back_populates="market", uselist=False, cascade="all, delete-orphan")
    offers = relationship("Offer", back_populates="market", cascade="all, delete-orphan")
    procurement_decision = relationship("ProcurementDecision", back_populates="market", uselist=False, cascade="all, delete-orphan")
    workflow = relationship("Workflow", back_populates="market", uselist=False, cascade="all, delete-orphan")
    
    @property
    def attributed_company(self):
        """Retourne l'entreprise attributaire"""
        return next((c for c in self.companies if c.is_attributed), None)
    
    @property
    def total_offers_amount(self):
        """Retourne le total des montants des offres"""
        return sum(c.offer_amount for c in self.companies if c.offer_amount)
    
    def __repr__(self):
        return f"<Market(id={self.id}, number='{self.market_number}', status='{self.status}')>"


class Company(Base):
    """Modèle Entreprise participante"""
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    
    # Informations entreprise
    name = Column(String(200), nullable=False)
    rc_number = Column(String(50))  # Registre de commerce
    if_number = Column(String(50))  # Identifiant fiscal
    address = Column(String(300))
    phone = Column(String(50))
    email = Column(String(100))
    
    # Offre
    offer_amount = Column(Float)
    offer_rank = Column(Integer)
    is_attributed = Column(Boolean, default=False)
    is_abnormally_low = Column(Boolean, default=False)
    is_abnormally_high = Column(Boolean, default=False)
    
    # Analyse
    technical_score = Column(Float)
    financial_score = Column(Float)
    total_score = Column(Float)
    
    # Observations
    observations = Column(Text)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relations
    market = relationship("Market", back_populates="companies")
    offers = relationship("Offer", back_populates="company", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.name}', attributed={self.is_attributed})>"
