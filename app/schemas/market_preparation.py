"""
Schémas Pydantic pour la préparation des marchés
Module 2: Préparation du dossier du marché
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.market_preparation import PreparationStatus


class PreparationDocumentBase(BaseModel):
    """Schéma de base pour un document de préparation"""
    document_type: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    is_required: bool = True


class PreparationDocumentResponse(PreparationDocumentBase):
    """Schéma de réponse pour un document"""
    id: int
    preparation_id: int
    file_path: str
    file_name: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    is_uploaded: bool = False
    validated: bool = False
    validated_by: Optional[int] = None
    validated_at: Optional[datetime] = None
    uploaded_by: Optional[int] = None
    uploaded_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PreparationHistoryBase(BaseModel):
    """Schéma de base pour un historique"""
    action: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class PreparationHistoryResponse(PreparationHistoryBase):
    """Schéma de réponse pour un historique"""
    id: int
    preparation_id: int
    user_id: int
    user_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PreparationAlertBase(BaseModel):
    """Schéma de base pour une alerte"""
    alert_type: str = Field(..., min_length=1, max_length=50)
    severity: str = Field(..., min_length=1, max_length=20)
    title: str = Field(..., min_length=1, max_length=200)
    message: Optional[str] = None


class PreparationAlertResponse(PreparationAlertBase):
    """Schéma de réponse pour une alerte"""
    id: int
    preparation_id: int
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MarketPreparationBase(BaseModel):
    """Schéma de base pour une préparation de marché"""
    planning_id: int = Field(..., gt=0)
    preparation_number: Optional[str] = Field(None, max_length=50)
    object: str = Field(..., min_length=3, max_length=300)
    procurement_type: Optional[str] = Field(None, max_length=50)
    procedure_type: Optional[str] = Field(None, max_length=50)
    requesting_service: Optional[str] = Field(None, max_length=200)
    responsible_id: Optional[int] = None
    duration: Optional[int] = Field(None, gt=0)
    location: Optional[str] = Field(None, max_length=200)
    estimated_budget: float = Field(..., ge=0)
    funding_source: Optional[str] = Field(None, max_length=200)
    progress_percentage: int = Field(default=0, ge=0, le=100)
    status: PreparationStatus = PreparationStatus.DRAFT
    observations: Optional[str] = None


class MarketPreparationCreate(MarketPreparationBase):
    """Schéma pour la création d'une préparation"""
    pass


class MarketPreparationUpdate(BaseModel):
    """Schéma pour la mise à jour d'une préparation"""
    preparation_number: Optional[str] = Field(None, max_length=50)
    object: Optional[str] = Field(None, min_length=3, max_length=300)
    procurement_type: Optional[str] = Field(None, max_length=50)
    procedure_type: Optional[str] = Field(None, max_length=50)
    requesting_service: Optional[str] = Field(None, max_length=200)
    responsible_id: Optional[int] = None
    duration: Optional[int] = Field(None, gt=0)
    location: Optional[str] = Field(None, max_length=200)
    estimated_budget: Optional[float] = Field(None, ge=0)
    funding_source: Optional[str] = Field(None, max_length=200)
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    status: Optional[PreparationStatus] = None
    observations: Optional[str] = None


class MarketPreparationResponse(MarketPreparationBase):
    """Schéma de réponse pour une préparation"""
    id: int
    # Validations
    technical_validation: bool = False
    technical_validator: Optional[int] = None
    technical_validation_date: Optional[datetime] = None
    technical_validation_comments: Optional[str] = None
    financial_validation: bool = False
    financial_validator: Optional[int] = None
    financial_validation_date: Optional[datetime] = None
    financial_validation_comments: Optional[str] = None
    administrative_validation: bool = False
    administrative_validator: Optional[int] = None
    administrative_validation_date: Optional[datetime] = None
    administrative_validation_comments: Optional[str] = None
    # Traçabilité
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
    # Relations
    documents: List[PreparationDocumentResponse] = []
    history: List[PreparationHistoryResponse] = []
    alerts: List[PreparationAlertResponse] = []

    class Config:
        from_attributes = True


class MarketPreparationListResponse(BaseModel):
    """Schéma de réponse pour la liste paginée"""
    items: List[MarketPreparationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ValidationRequest(BaseModel):
    """Schéma pour une demande de validation"""
    validation_type: str = Field(..., pattern="^(technical|financial|administrative)$")
    comments: Optional[str] = None
    approved: bool = True


class ValidationResponse(BaseModel):
    """Schéma de réponse pour une validation"""
    success: bool
    message: str
    validation_date: Optional[datetime] = None
