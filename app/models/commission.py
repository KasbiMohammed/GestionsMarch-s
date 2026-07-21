"""
Modèles pour la gestion des commissions
Module 4: Gestion des commissions
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from enum import Enum

from app.database import Base


class CommissionType(str, Enum):
    """Types de commissions"""
    OPENING = "ouverture_plis"
    TECHNICAL = "analyse_technique"
    FINANCIAL = "analyse_financiere"
    ATTRIBUTION = "attribution"
    APPEL_OFFRES = "appel_offres"


class CommissionStatus(str, Enum):
    """Statuts de commission"""
    PLANNED = "planifiée"
    CONVOKED = "convquée"
    IN_PROGRESS = "en_cours"
    COMPLETED = "terminée"
    CANCELLED = "annulée"


class Commission(Base):
    """Commission d'attribution ou d'analyse"""
    __tablename__ = "commissions"
    
    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    
    # Informations générales
    commission_type = Column(SQLEnum(CommissionType), nullable=False)
    reference = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Date et lieu
    planned_date = Column(DateTime, nullable=False)
    planned_time = Column(String(10), nullable=True)
    location = Column(String(200), nullable=True)
    
    # Statut
    status = Column(SQLEnum(CommissionStatus), default=CommissionStatus.PLANNED)
    
    # Quorum
    required_members = Column(Integer, default=3)
    actual_members = Column(Integer, default=0)
    quorum_reached = Column(Boolean, default=False)
    
    # PV
    pv_content = Column(Text, nullable=True)
    pv_generated = Column(Boolean, default=False)
    pv_generated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    pv_generated_at = Column(DateTime, nullable=True)
    
    # Signatures
    signatures = Column(JSON, nullable=True)  # Liste des signatures électroniques
    
    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    market = relationship("Market", back_populates="commissions")
    members = relationship("CommissionMember", back_populates="commission", cascade="all, delete-orphan")
    convocations = relationship("CommissionConvocation", back_populates="commission", cascade="all, delete-orphan")


class CommissionMember(Base):
    """Membre de commission"""
    __tablename__ = "commission_members"
    
    id = Column(Integer, primary_key=True, index=True)
    commission_id = Column(Integer, ForeignKey("commissions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Rôle dans la commission
    role = Column(String(50), nullable=False)  # président, secrétaire, membre
    is_president = Column(Boolean, default=False)
    
    # Présence
    attended = Column(Boolean, nullable=True)
    attendance_time = Column(DateTime, nullable=True)
    
    # Signature
    signature = Column(String(500), nullable=True)  # Chemin ou hash de signature
    signed_at = Column(DateTime, nullable=True)
    
    # Traçabilité
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    commission = relationship("Commission", back_populates="members")
    user = relationship("User")


class CommissionConvocation(Base):
    """Convocation à une commission"""
    __tablename__ = "commission_convocations"
    
    id = Column(Integer, primary_key=True, index=True)
    commission_id = Column(Integer, ForeignKey("commissions.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("commission_members.id"), nullable=False)
    
    # Date d'envoi
    sent_at = Column(DateTime, nullable=True)
    sent_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Méthode d'envoi
    sending_method = Column(String(50), nullable=True)  # email, courrier, sms
    
    # Réponse
    response = Column(String(50), nullable=True)  # accepté, refusé, absent
    response_at = Column(DateTime, nullable=True)
    
    # Traçabilité
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    commission = relationship("Commission", back_populates="convocations")
    member = relationship("CommissionMember")
