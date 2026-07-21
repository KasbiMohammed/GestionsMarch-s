"""
Modèles pour la gestion des documents et pièces jointes
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class DocumentType(str, enum.Enum):
    """Types de documents"""
    CPS = "cps"
    BPU = "bpu"
    DQE = "dqe"
    CAHIER_PRESCRIPTIONS = "cahier_prescriptions"
    OFFRE = "offre"
    PROCES_VERBAL = "proces_verbal"
    CONTRAT = "contrat"
    ORDRE_SERVICE = "ordre_service"
    ATTACHEMENT = "attachement"
    DECOMPTE = "decompte"
    AVENANT = "avenant"
    RECEPTION = "reception"
    RAPPORT = "rapport"
    AUTRE = "autre"


class DocumentCategory(str, enum.Enum):
    """Catégories de documents"""
    ADMINISTRATIF = "administratif"
    TECHNIQUE = "technique"
    FINANCIER = "financier"
    JURIDIQUE = "juridique"
    EXECUTION = "execution"


class Document(Base):
    """Modèle Document"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    stage_id = Column(Integer, ForeignKey("stages.id"), nullable=True)
    
    # Informations du document
    name = Column(String(200), nullable=False)
    description = Column(Text)
    document_type = Column(Enum(DocumentType))
    category = Column(Enum(DocumentCategory))
    
    # Fichier
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Float)  # Taille en octets
    file_type = Column(String(50))  # MIME type
    file_hash = Column(String(64))  # SHA-256 hash
    
    # Version
    version = Column(Integer, default=1)
    is_current_version = Column(Boolean, default=True)
    previous_version_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    
    # Métadonnées
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    
    # Validation
    is_validated = Column(Boolean, default=False)
    validated_by = Column(Integer, ForeignKey("users.id"))
    validation_date = Column(DateTime)
    
    # Observations
    observations = Column(Text)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relations
    market = relationship("Market", back_populates="documents")
    previous_version = relationship("Document", remote_side=[id])
    
    def __repr__(self):
        return f"<Document(id={self.id}, name='{self.name}', type='{self.document_type}')>"
