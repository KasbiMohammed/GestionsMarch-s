"""
Modèles de gestion des délais réglementaires
Module dédié à la gestion intelligente des délais conformément au Décret n°2-22-431
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, Float, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum
import enum

from app.database import Base


class DeadlineType(str, enum.Enum):
    """Types de délais réglementaires"""
    # Publication
    PUBLICATION_PMMP = "publication_pmmp"
    PUBLICATION_PRESSE = "publication_presse"
    
    # Délais avant ouverture
    DELAI_OUVERTURE_PLIS = "delai_ouverture_plis"
    
    # Éclaircissements
    DELAI_ECLAIRCISSEMENT = "delai_eclaircissement"
    DELAI_REPONSE_ECLAIRCISSEMENT = "delai_reponse_eclaircissement"
    
    # Reports
    REPORT_OUVERTURE = "report_ouverture"
    
    # Ouverture et évaluation
    OUVERTURE_PLIS = "ouverture_plis"
    VALIDITE_OFFRES = "validite_offres"
    
    # Délai d'attente (standstill)
    DELAI_ATTENTE_APPROBATION = "delai_attente_approbation"
    
    # Notification et ordre de service
    NOTIFICATION_ATTRIBUTION = "notification_attribution"
    ORDRE_SERVICE = "ordre_service"
    
    # Exécution
    DEBUT_EXECUTION = "debut_execution"
    FIN_EXECUTION = "fin_execution"
    
    # Réceptions
    RECEPTION_PROVISOIRE = "reception_provisoire"
    RECEPTION_DEFINITIVE = "reception_definitive"
    
    # Garantie
    GARANTIE_SOUMISSIONNAIRE = "garantie_soumissionnaire"
    GARANTIE_EXECUTION = "garantie_execution"
    LIBERATION_GARANTIE = "liberation_garantie"
    
    # Réclamations et recours
    DELAI_RECLAMATION = "delai_reclamation"
    DELAI_RECOURS = "delai_recours"
    
    # Paiements
    DELAI_PAIEMENT = "delai_paiement"
    DELAI_PAIEMENT_PARTIEL = "delai_paiement_partiel"
    
    # Autres
    DELAI_CONSULTATION = "delai_consultation"
    DELAI_PRESLECTION = "delai_preselection"
    DELAI_NEGOCIATION = "delai_negociation"


class AlertLevel(str, enum.Enum):
    """Niveaux d'alerte"""
    NORMAL = "normal"
    ATTENTION = "attention"
    IMPORTANT = "important"
    CRITIQUE = "critique"
    DEPASSE = "depasse"


class DeadlineStatus(str, enum.Enum):
    """Statut d'un délai"""
    ACTIF = "actif"
    TERMINE = "termine"
    DEPASSE = "depasse"
    ANNULE = "annule"
    SUSPENDU = "suspendu"


class NotificationStatus(str, enum.Enum):
    """Statut d'une notification"""
    EN_ATTENTE = "en_attente"
    ENVOYE = "envoye"
    LU = "lu"
    IGNORE = "ignore"


class DeadlineSettings(Base):
    """Configuration des seuils d'alerte pour les types de délais"""
    __tablename__ = "deadline_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    deadline_type = Column(SQLEnum(DeadlineType), unique=True, nullable=False, index=True)
    type_name = Column(String(200), nullable=False)  # Nom lisible du type de délai
    description = Column(Text, nullable=True)
    
    # Seuils d'alerte en jours avant l'échéance
    j1 = Column(Integer, default=30)  # Seuil d'alerte normale (30 jours avant)
    j2 = Column(Integer, default=15)  # Seuil d'alerte importante (15 jours avant)
    j3 = Column(Integer, default=7)   # Seuil d'alerte critique (7 jours avant)
    critique = Column(Integer, default=3)  # Seuil critique urgent (3 jours avant)
    
    # Activation du type de délai
    activation = Column(Boolean, default=True)
    
    # Délai par défaut en jours (pour calcul automatique)
    default_days = Column(Integer, nullable=True)
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)


class Deadline(Base):
    """Délai réglementaire pour un marché ou une procédure"""
    __tablename__ = "deadlines"
    
    id = Column(Integer, primary_key=True, index=True)
    deadline_type = Column(SQLEnum(DeadlineType), nullable=False, index=True)
    
    # Référence à l'entité concernée
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=True, index=True)
    planning_id = Column(Integer, ForeignKey("market_plannings.id"), nullable=True, index=True)
    offer_id = Column(Integer, ForeignKey("offers.id"), nullable=True, index=True)
    
    # Dates
    start_date = Column(Date, nullable=False)  # Date de départ
    due_date = Column(Date, nullable=False)    # Date limite
    completed_date = Column(Date, nullable=True)  # Date de réalisation effective
    
    # Calculs automatiques
    days_remaining = Column(Integer, default=0)
    days_overdue = Column(Integer, default=0)
    alert_level = Column(SQLEnum(AlertLevel), default=AlertLevel.NORMAL)
    status = Column(SQLEnum(DeadlineStatus), default=DeadlineStatus.ACTIF)
    
    # Informations complémentaires
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    reference = Column(String(100), nullable=True)  # Référence réglementaire
    
    # Gestion des reports
    original_due_date = Column(Date, nullable=True)  # Date limite initiale
    extension_count = Column(Integer, default=0)     # Nombre de reports
    extension_reason = Column(Text, nullable=True)
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relations
    settings = relationship("DeadlineSettings", foreign_keys=[deadline_type], primaryjoin="Deadline.deadline_type == DeadlineSettings.deadline_type")
    alerts = relationship("DeadlineAlert", back_populates="deadline", cascade="all, delete-orphan")
    notifications = relationship("DeadlineNotification", back_populates="deadline", cascade="all, delete-orphan")
    
    # Relations avec les entités existantes
    market = relationship("Market", foreign_keys=[market_id])
    planning = relationship("MarketPlanning", foreign_keys=[planning_id])
    offer = relationship("Offer", foreign_keys=[offer_id])


class DeadlineAlert(Base):
    """Alertes générées pour les délais"""
    __tablename__ = "deadline_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    deadline_id = Column(Integer, ForeignKey("deadlines.id"), nullable=False, index=True)
    
    alert_level = Column(SQLEnum(AlertLevel), nullable=False)
    alert_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # État de l'alerte
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    
    # Message de l'alerte
    message = Column(Text, nullable=False)
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    deadline = relationship("Deadline", back_populates="alerts")


class DeadlineNotification(Base):
    """Notifications envoyées pour les délais"""
    __tablename__ = "deadline_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    deadline_id = Column(Integer, ForeignKey("deadlines.id"), nullable=False, index=True)
    
    # Destinataire
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Contenu
    title = Column(String(300), nullable=False)
    message = Column(Text, nullable=False)
    
    # Statut
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.EN_ATTENTE)
    
    # Dates
    scheduled_date = Column(DateTime, nullable=True)  # Date prévue d'envoi
    sent_date = Column(DateTime, nullable=True)       # Date d'envoi effectif
    read_date = Column(DateTime, nullable=True)       # Date de lecture
    
    # Type de notification
    notification_type = Column(String(50), default="email")  # email, sms, dashboard
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    deadline = relationship("Deadline", back_populates="notifications")
    user = relationship("User", foreign_keys=[user_id])
