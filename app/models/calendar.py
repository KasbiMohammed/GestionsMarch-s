"""
Modèles pour le Calendrier Intelligent
Module dédié - Agrégation des événements et suivi budgétaire
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from enum import Enum
import enum

from app.database import Base


class EventType(str, enum.Enum):
    """Types d'événements du calendrier"""
    PLANNIFICATION = "plannification"  # Planification
    PREPARATION = "preparation"  # Préparation
    PUBLICATION = "publication"  # Publication
    COMMISSION = "commission"  # Commission
    OUVERTURE_PLIS = "ouverture_plis"  # Ouverture des plis
    ATTRIBUTION = "attribution"  # Attribution
    NOTIFICATION = "notification"  # Notification
    ORDRE_SERVICE = "ordre_service"  # Ordre de service
    EXECUTION = "execution"  # Exécution  
    RECEPTION = "reception"  # Réception
    ALERTE = "alerte"  # Alerte
    DELAI = "delai"  # Délai réglementaire
    AUTRE = "autre"  # Autre


class CalendarEvent(Base):
    """Événement agrégé dans le calendrier"""
    __tablename__ = "calendar_events"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Référence à l'entité source
    source_module = Column(String(50), nullable=False, index=True)  # market, planning, stage, deadline, commission
    source_entity_id = Column(Integer, nullable=True, index=True)  # ID de l'entité source
    source_entity_type = Column(String(50), nullable=True)  # Type de l'entité (market, stage, deadline, etc.)
    
    # Informations de l'événement
    event_type = Column(String(50), nullable=False, index=True)  # EventType
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    
    # Dates
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=True, index=True)
    is_all_day = Column(Boolean, default=False)
    
    # Métadonnées
    service = Column(String(100), nullable=True, index=True)
    responsible = Column(String(100), nullable=True, index=True)
    procedure = Column(String(100), nullable=True, index=True)
    status = Column(String(50), nullable=True, index=True)
    priority = Column(String(20), nullable=True)  # low, medium, high
    
    # Couleur et affichage
    color = Column(String(7), nullable=True)  # Code hexadécimal
    icon = Column(String(50), nullable=True)  # Classe d'icône Bootstrap
    
    # Métadonnées supplémentaires
    doc_metadata = Column(JSON, nullable=True)
    
    # Synchronisation
    is_synced = Column(Boolean, default=True)
    last_synced_at = Column(DateTime, default=datetime.utcnow)
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BudgetTracking(Base):
    """Suivi budgétaire annuel"""
    __tablename__ = "budget_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Période
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=True, index=True)  # NULL pour le total annuel
    
    # Service (NULL pour le global)
    service = Column(String(100), nullable=True, index=True)
    
    # Montants budgétaires
    budget_voted = Column(Float, default=0.0)  # Budget voté
    budget_engaged = Column(Float, default=0.0)  # Budget engagé
    budget_consumed = Column(Float, default=0.0)  # Budget consommé
    budget_remaining = Column(Float, default=0.0)  # Budget restant
    
    # Répartition par procédure
    procedure_breakdown = Column(JSON, nullable=True)  # {"procedure": amount}
    
    # Statistiques
    total_markets = Column(Integer, default=0)
    total_amount = Column(Float, default=0.0)
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
