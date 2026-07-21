"""
Modèles pour les alertes intelligentes
Module 11: Alertes intelligentes
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey,Float , Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum

from app.database import Base


class AlertType(str, Enum):
    """Types d'alertes"""
    MARKET_DELAY = "marché_en_retard"
    GUARANTEE_EXPIRY = "expiration_garantie"
    PROVISIONAL_GUARANTEE = "caution_provisoire"
    DEFINITIVE_GUARANTEE = "caution_définitive"
    DEADLINE_EXPIRY = "fin_délai"
    RECLAMATION_DEADLINE = "délai_réclamation"
    OFFER_VALIDITY = "validité_offre"
    PROVISIONAL_RECEPTION = "réception_provisoire"
    DEFINITIVE_RECEPTION = "réception_définitive"
    WARRANTY_EXPIRY = "fin_garantie"
    BUDGET_OVERRUN = "dépassement_budgétaire"
    CREDIT_CONSUMPTION = "consommation_crédits"
    STAGE_DELAY = "étape_en_retard"


class AlertSeverity(str, Enum):
    """Gravité des alertes"""
    LOW = "faible"
    MEDIUM = "moyenne"
    HIGH = "haute"
    CRITICAL = "critique"


class AlertStatus(str, Enum):
    """Statuts des alertes"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acquittée"
    RESOLVED = "résolue"
    DISMISSED = "ignorée"


class Alert(Base):
    """Alerte intelligente"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Type et gravité
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    severity = Column(SQLEnum(AlertSeverity), default=AlertSeverity.MEDIUM)
    
    # Entité concernée
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=True)
    stage_id = Column(Integer, ForeignKey("stages.id"), nullable=True)
    guarantee_id = Column(Integer, ForeignKey("guarantees.id"), nullable=True)
    offer_id = Column(Integer, ForeignKey("offers.id"), nullable=True)
    
    # Message
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Dates
    trigger_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=True)
    
    # Statut
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.ACTIVE)
    
    # Notifications
    notification_sent = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime, nullable=True)
    
    # Résolution
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Traçabilité
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    market = relationship("Market", back_populates="alerts")
    stage = relationship("Stage", back_populates="alerts")
    guarantee = relationship("Guarantee")
    offer = relationship("Offer")


class AlertRule(Base):
    """Règle de génération d'alerte"""
    __tablename__ = "alert_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Configuration
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    
    # Conditions
    condition = Column(Text, nullable=False)  # Expression de condition
    threshold_days = Column(Integer, nullable=True)  # Jours avant l'échéance
    threshold_percentage = Column(Float, nullable=True)  # Pourcentage
    
    # Message template
    title_template = Column(String(200), nullable=False)
    message_template = Column(Text, nullable=False)
    
    # Actif
    is_active = Column(Boolean, default=True)
    
    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
