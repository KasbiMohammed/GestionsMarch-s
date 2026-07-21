"""
Modèles pour la réception et gestion des offres
Module 5 & 6: Publication PMMP et Réception des offres
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from enum import Enum

from app.database import Base


class PublicationStatus(str, Enum):
    """Statuts de publication"""
    DRAFT = "brouillon"
    PENDING = "en_attente"
    PUBLISHED = "publié"
    WITHDRAWN = "retiré"
    ARCHIVED = "archivé"


class PMMPPublication(Base):
    """Publication sur le portail PMMP"""
    __tablename__ = "pmmp_publications"
    
    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    
    # Informations PMMP
    pmmp_reference = Column(String(100), nullable=True)
    pmmp_url = Column(String(500), nullable=True)
    
    # Dates de publication
    publication_date = Column(DateTime, nullable=True)
    closing_date = Column(DateTime, nullable=True)
    opening_date = Column(DateTime, nullable=True)
    
    # Statut
    status = Column(SQLEnum(PublicationStatus), default=PublicationStatus.DRAFT)
    
    # Statistiques
    downloads_count = Column(Integer, default=0)
    views_count = Column(Integer, default=0)
    
    # Traçabilité
    published_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    market = relationship("Market", back_populates="pmmp_publication")


class OfferStatus(str, Enum):
    """Statuts des offres"""
    RECEIVED = "reçue"
    ADMISSIBLE = "admissible"
    INADMISSIBLE = "inadmissible"
    WITHDRAWN = "retirée"
    SELECTED = "sélectionnée"
    REJECTED = "rejetée"


class Offer(Base):
    """Offre d'un concurrent"""
    __tablename__ = "offers"
    
    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Informations générales
    offer_reference = Column(String(100), nullable=False)
    submission_date = Column(DateTime, nullable=False)
    
    # Montant de l'offre
    financial_amount = Column(Float, nullable=False)
    currency = Column(String(10), default="MAD")
    
    # Statut
    status = Column(SQLEnum(OfferStatus), default=OfferStatus.RECEIVED)
    
    # Conformité
    administrative_compliance = Column(Boolean, nullable=True)
    technical_compliance = Column(Boolean, nullable=True)
    overall_compliance = Column(Boolean, nullable=True)
    
    # Signature électronique
    digital_signature = Column(String(500), nullable=True)
    signature_verified = Column(Boolean, default=False)
    
    # Classement
    rank = Column(Integer, nullable=True)
    score = Column(Float, nullable=True)
    
    # Observations
    observations = Column(Text, nullable=True)
    
    # Traçabilité
    received_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    market = relationship("Market", back_populates="offers")
    company = relationship("Company", back_populates="offers")
    documents = relationship("OfferDocument", back_populates="offer", cascade="all, delete-orphan")



class OfferDocument(Base):
    """Document d'offre"""
    __tablename__ = "offer_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(Integer, ForeignKey("offers.id"), nullable=False)
    
    # Type de document
    document_type = Column(String(50), nullable=False)  # administratif, technique, financier
    document_name = Column(String(200), nullable=False)
    
    # Fichier
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    file_hash = Column(String(100), nullable=True)
    
    # Validation
    validated = Column(Boolean, default=False)
    validated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    validation_comments = Column(Text, nullable=True)
    
    # Traçabilité
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    offer = relationship("Offer", back_populates="documents")
