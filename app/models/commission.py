"""
Modèles pour la gestion des commissions
Module 4: Constitution et gestion de la commission
Relation: 1 workflow de validation → 1 commission
Une commission peut avoir plusieurs séances indépendantes
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from enum import Enum

from app.database import Base


class CommissionStatus(str, Enum):
    """Statuts de commission"""
    TO_BE_CONSTITUTED = "a_constituer"
    CONSTITUTED = "constituee"
    SESSIONS_PLANNED = "seances_planifiees"
    SESSION_IN_PROGRESS = "seance_en_cours"
    SESSION_CLOSED = "seance_cloturee"
    COMMISSION_CLOSED = "commission_cloturee"


class SessionStatus(str, Enum):
    """Statuts de séance"""
    PLANNED = "planifiee"
    POSTPONED = "reportee"
    IN_PROGRESS = "en_cours"
    SUSPENDED = "suspendue"
    CLOSED = "cloturee"
    CANCELLED = "annulee"


class MemberRole(str, Enum):
    """Rôles des membres"""
    PRESIDENT = "president"
    MEMBER = "membre"
    SUBSTITUTE = "suppleant"
    SECRETARY = "secretaire"


class Commission(Base):
    """Commission d'attribution"""
    __tablename__ = "commissions"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("validation_workflows.id"), nullable=False, unique=True)
    commission_number = Column(String(50), unique=True, nullable=True)
    
    # Informations générales
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Statut
    status = Column(SQLEnum(CommissionStatus), default=CommissionStatus.TO_BE_CONSTITUTED)
    
    # Dates
    constituted_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    
    # Observations globales
    observations = Column(Text, nullable=True)
    
    # Suppression logique
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    workflow = relationship("ValidationWorkflow", back_populates="commission")
    members = relationship("CommissionMember", back_populates="commission", cascade="all, delete-orphan")
    sessions = relationship("CommissionSession", back_populates="commission", cascade="all, delete-orphan")
    alerts = relationship("CommissionAlert", back_populates="commission", cascade="all, delete-orphan")
    history = relationship("CommissionHistory", back_populates="commission", cascade="all, delete-orphan")
    publications = relationship("Publication", back_populates="commission", cascade="all, delete-orphan")


class CommissionMember(Base):
    """Membre de commission"""
    __tablename__ = "commission_members"
    
    id = Column(Integer, primary_key=True, index=True)
    commission_id = Column(Integer, ForeignKey("commissions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Rôle
    role = Column(SQLEnum(MemberRole), nullable=False)
    is_president = Column(Boolean, default=False)
    is_secretary = Column(Boolean, default=False)
    
    # Informations du membre
    user_name = Column(String(200), nullable=True)
    user_function = Column(String(200), nullable=True)
    user_department = Column(String(200), nullable=True)
    
    # Suppléant
    substitute_for_id = Column(Integer, ForeignKey("commission_members.id"), nullable=True)
    
    # Traçabilité
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    commission = relationship("Commission", back_populates="members")
    user = relationship("User")
    substitute_for = relationship("CommissionMember", remote_side=[id])


class CommissionSession(Base):
    """Séance de commission (indépendante)"""
    __tablename__ = "commission_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    commission_id = Column(Integer, ForeignKey("commissions.id"), nullable=False)
    
    # Numéro et objet de séance
    session_number = Column(Integer, nullable=False)
    session_title = Column(String(200), nullable=False)
    session_type = Column(String(100), nullable=True)  # ouverture_plis, verification_dossiers, evaluation_technique, evaluation_financiere, attribution
    
    # Date, heure et lieu
    planned_date = Column(DateTime, nullable=False)
    planned_time = Column(String(10), nullable=True)
    location = Column(String(200), nullable=True)
    
    # Statut
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.PLANNED)
    
    # Dates réelles
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    
    # Ordre du jour
    agenda = Column(Text, nullable=True)
    
    # Membres présents et absents
    members_present = Column(JSON, nullable=True)  # Liste des IDs des membres présents
    members_absent = Column(JSON, nullable=True)  # Liste des IDs des membres absents
    
    # Observations
    observations = Column(Text, nullable=True)
    
    # Décisions
    decisions = Column(Text, nullable=True)
    
    # Procès-verbal
    pv_content = Column(Text, nullable=True)
    pv_generated = Column(Boolean, default=False)
    pv_generated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    pv_generated_at = Column(DateTime, nullable=True)
    pv_attachment_path = Column(String(500), nullable=True)
    pv_attachment_name = Column(String(255), nullable=True)
    
    # Pièces jointes
    attachments = Column(JSON, nullable=True)  # Liste des pièces jointes
    
    # Report ou suspension
    postponed_to = Column(DateTime, nullable=True)
    postponed_reason = Column(Text, nullable=True)
    suspended_reason = Column(Text, nullable=True)
    
    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    commission = relationship("Commission", back_populates="sessions")
    pv_generator = relationship("User", foreign_keys=[pv_generated_by])


class CommissionAlert(Base):
    """Alertes pour la commission"""
    __tablename__ = "commission_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    commission_id = Column(Integer, ForeignKey("commissions.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("commission_sessions.id"), nullable=True)
    
    # Type d'alerte
    alert_type = Column(String(50), nullable=False)  # convocation_not_sent, session_upcoming, session_postponed, pv_missing, members_absent, delay
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    
    # Message
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    
    # Statut
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Traçabilité
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    commission = relationship("Commission", back_populates="alerts")
    session = relationship("CommissionSession")
    resolver = relationship("User", foreign_keys=[resolved_by])


class CommissionHistory(Base):
    """Historique de commission"""
    __tablename__ = "commission_history"
    
    id = Column(Integer, primary_key=True, index=True)
    commission_id = Column(Integer, ForeignKey("commissions.id"), nullable=False)
    
    # Action
    action = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Détails
    session_id = Column(Integer, nullable=True)
    member_id = Column(Integer, nullable=True)
    
    # Utilisateur
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_name = Column(String(100), nullable=True)
    
    # Traçabilité
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    commission = relationship("Commission", back_populates="history")
    user = relationship("User")

