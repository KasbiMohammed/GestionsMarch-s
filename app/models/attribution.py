"""
Modèles pour l'attribution des marchés
Module 8: Attribution
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum

from app.database import Base


class AttributionStatus(str, Enum):
    """Statuts d'attribution"""
    PROVISIONAL = "provisoire"
    NOTIFIED = "notifié"
    RECLAMATION_PENDING = "reclamation_en_attente"
    RECLAMATION_PROCESSED = "reclamation_traitée"
    DEFINITIVE = "définitif"
    APPROVED = "approuvé"
    VISA = "visa"
    CANCELLED = "annulé"


class Attribution(Base):
    """Attribution de marché"""
    __tablename__ = "attributions"
    
    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    offer_id = Column(Integer, ForeignKey("offers.id"), nullable=False)
    
    # Montant d'attribution
    attributed_amount = Column(Float, nullable=False)
    currency = Column(String(10), default="MAD")
    
    # Statut
    status = Column(SQLEnum(AttributionStatus), default=AttributionStatus.PROVISIONAL)
    
    # Attribution provisoire
    provisional_decision_date = Column(DateTime, nullable=True)
    provisional_decision_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    provisional_pv_reference = Column(String(100), nullable=True)
    
    # Notification
    notification_date = Column(DateTime, nullable=True)
    notification_method = Column(String(50), nullable=True)
    notification_reference = Column(String(100), nullable=True)
    
    # Réclamations
    has_reclamation = Column(Boolean, default=False)
    reclamation_date = Column(DateTime, nullable=True)
    reclamation_content = Column(Text, nullable=True)
    reclamation_response = Column(Text, nullable=True)
    reclamation_response_date = Column(DateTime, nullable=True)
    
    # Attribution définitive
    definitive_decision_date = Column(DateTime, nullable=True)
    definitive_decision_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    definitive_pv_reference = Column(String(100), nullable=True)
    
    # Approbation
    approval_date = Column(DateTime, nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approval_reference = Column(String(100), nullable=True)
    
    # Visa
    visa_date = Column(DateTime, nullable=True)
    visa_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    visa_reference = Column(String(100), nullable=True)
    
    # Notification du titulaire
    awardee_notification_date = Column(DateTime, nullable=True)
    awardee_notification_method = Column(String(50), nullable=True)
    
    # Observations
    observations = Column(Text, nullable=True)
    
    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    market = relationship("Market", back_populates="attribution")
    offer = relationship("Offer")


class Reclamation(Base):
    """Réclamation contre une attribution"""
    __tablename__ = "reclamations"
    
    id = Column(Integer, primary_key=True, index=True)
    attribution_id = Column(Integer, ForeignKey("attributions.id"), nullable=False)
    claimant_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Contenu de la réclamation
    reclamation_date = Column(DateTime, nullable=False)
    reclamation_type = Column(String(50), nullable=True)  # procédure, évaluation, autre
    content = Column(Text, nullable=False)
    
    # Traitement
    processed = Column(Boolean, default=False)
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    processed_at = Column(DateTime, nullable=True)
    response = Column(Text, nullable=True)
    
    # Décision
    accepted = Column(Boolean, nullable=True)
    decision_date = Column(DateTime, nullable=True)
    decision_reference = Column(String(100), nullable=True)
    
    # Traçabilité
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    attribution = relationship("Attribution")
    claimant = relationship("Company")
