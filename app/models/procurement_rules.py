"""
Modèles pour le choix automatique de la procédure
Module 3: Choix automatique de la procédure
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum

from app.database import Base


class ProcurementMethod(str, Enum):
    """Modes de passation des marchés"""
    BON_COMMANDE = "bon_commande"
    AO_OUVERT = "appel_offres_ouvert"
    AO_OUVERT_SIMPLIFIE = "appel_offres_ouvert_simplifie"
    AO_RESTREINT = "appel_offres_restreint"
    CONCOURS = "concours"
    DIALOGUE_COMPETITIF = "dialogue_competitif"
    MARCHE_NEGOCIE = "marche_negocie"
    MARCHE_CADRE = "marche_cadre"
    MARCHE_RECONDUCTIBLE = "marche_reconductible"


class MarketNature(str, Enum):
    """Nature du marché"""
    TRAVAUX = "travaux"
    FOURNITURES = "fournitures"
    SERVICES = "services"
    ETUDES = "etudes"


class ProcurementRule(Base):
    """Règle de choix de procédure"""
    __tablename__ = "procurement_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Conditions de la règle
    min_amount = Column(Float, nullable=True)
    max_amount = Column(Float, nullable=True)
    market_nature = Column(String(50), nullable=True)
    
    # Procédure résultante
    procurement_method = Column(SQLEnum(ProcurementMethod), nullable=False)
    
    # Référence réglementaire
    regulatory_reference = Column(String(200), nullable=True)
    article_reference = Column(String(100), nullable=True)
    
    # Description
    description = Column(Text, nullable=True)
    
    # Conditions supplémentaires
    conditions = Column(Text, nullable=True)
    
    # Actif
    is_active = Column(Boolean, default=True)
    
    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProcurementDecision(Base):
    """Décision de procédure pour un marché"""
    __tablename__ = "procurement_decisions"
    
    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    preparation_id = Column(Integer, ForeignKey("market_preparations.id"), nullable=True)
    
    # Données d'entrée
    estimated_amount = Column(Float, nullable=False)
    market_nature = Column(String(50), nullable=False)
    
    # Procédure choisie
    chosen_method = Column(SQLEnum(ProcurementMethod), nullable=False)
    applied_rule_id = Column(Integer, ForeignKey("procurement_rules.id"), nullable=True)
    
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
    market = relationship("Market", back_populates="procurement_decision")
    applied_rule = relationship("ProcurementRule")
