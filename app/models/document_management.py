"""
Modèles pour la gestion documentaire
Module 10: Gestion documentaire
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum

from app.database import Base


class DocumentCategory(str, Enum):
    """Catégories de documents"""
    CPS = "cps"
    BPU = "bpu"
    DQE = "dqe"
    ACTE_ENGAGEMENT = "acte_engagement"
    PV = "pv"
    RAPPORT = "rapport"
    PLAN = "plan"
    PHOTO = "photo"
    CORRESPONDANCE = "correspondance"
    ORDRE_SERVICE = "ordre_service"
    DECOMPTE = "decompte"
    FACTURE = "facture"
    AVENANT = "avenant"
    AUTRE = "autre"


class DocumentVersion(Base):
    """Version d'un document"""
    __tablename__ = "document_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    
    # Informations de version
    version_number = Column(Integer, nullable=False)
    change_description = Column(Text, nullable=True)
    
    # Fichier
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    file_hash = Column(String(100), nullable=True)
    
    # Traçabilité
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    document = relationship("Document")


class DocumentAccess(Base):
    """Accès aux documents"""
    __tablename__ = "document_access"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Permissions
    can_view = Column(Boolean, default=True)
    can_download = Column(Boolean, default=True)
    can_edit = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    
    # Traçabilité
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    granted_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations

    user = relationship("User", foreign_keys=[user_id])
    granter = relationship("User", foreign_keys=[granted_by])
