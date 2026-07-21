"""
Modèles pour l'historique des modifications et l'audit trail
"""

from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class ActionType(str, enum.Enum):
    """Types d'actions"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VALIDATE = "validate"
    APPROVE = "approve"
    REJECT = "reject"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    EXPORT = "export"
    LOGIN = "login"
    LOGOUT = "logout"


class EntityType(str, enum.Enum):
    """Types d'entités"""
    MARKET = "market"
    STAGE = "stage"
    DOCUMENT = "document"
    USER = "user"
    COMPANY = "company"


class History(Base):
    """Modèle Historique des modifications"""
    __tablename__ = "histories"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Action et entité
    action_type = Column(Enum(ActionType), nullable=False)
    entity_type = Column(Enum(EntityType), nullable=False)
    entity_id = Column(Integer, nullable=False)
    
    # Relations
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Détails de l'action
    description = Column(Text)
    old_values = Column(JSON)  # Valeurs avant modification
    new_values = Column(JSON)  # Valeurs après modification
    changed_fields = Column(JSON)  # Liste des champs modifiés
    
    # Métadonnées
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relations
    market = relationship("Market", back_populates="histories")
    user = relationship("User", foreign_keys=[user_id], back_populates="created_histories")
    
    def __repr__(self):
        return f"<History(id={self.id}, action='{self.action_type}', entity='{self.entity_type}')>"
