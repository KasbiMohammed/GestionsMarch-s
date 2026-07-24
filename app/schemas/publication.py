"""
Schémas Pydantic pour la gestion des publications
Module 5: Publication de l'avis et lancement de la consultation
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.publication import (
    PublicationType,
    PublicationStatus,
    ProcedureType,
    SupportType,
)


class PublicationSupportBase(BaseModel):
    """Schéma de base pour un support de publication"""
    support_type: SupportType
    support_name: Optional[str] = None
    publication_date: Optional[datetime] = None
    reference: Optional[str] = None
    cost: Optional[float] = None


class PublicationSupportResponse(PublicationSupportBase):
    """Schéma de réponse pour un support de publication"""
    id: int
    publication_id: int
    attachment_path: Optional[str] = None
    attachment_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PublicationDeadlineBase(BaseModel):
    """Schéma de base pour une échéance de publication"""
    deadline_type: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    deadline_date: datetime
    deadline_time: Optional[str] = None


class PublicationDeadlineResponse(PublicationDeadlineBase):
    """Schéma de réponse pour une échéance de publication"""
    id: int
    publication_id: int
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    alert_sent: bool = False
    alert_sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PublicationAlertBase(BaseModel):
    """Schéma de base pour une alerte de publication"""
    alert_type: str = Field(..., min_length=1, max_length=50)
    severity: str = Field(..., min_length=1, max_length=20)
    title: str = Field(..., min_length=1, max_length=200)
    message: Optional[str] = None
    deadline_id: Optional[int] = None


class PublicationAlertResponse(PublicationAlertBase):
    """Schéma de réponse pour une alerte de publication"""
    id: int
    publication_id: int
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PublicationHistoryBase(BaseModel):
    """Schéma de base pour l'historique de publication"""
    action: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    status_change: Optional[str] = None


class PublicationHistoryResponse(PublicationHistoryBase):
    """Schéma de réponse pour l'historique de publication"""
    id: int
    publication_id: int
    user_id: int
    user_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PublicationBase(BaseModel):
    """Schéma de base pour une publication"""
    commission_id: int = Field(..., gt=0)
    publication_number: Optional[str] = Field(None, max_length=50)
    publication_type: PublicationType = PublicationType.INITIAL
    notice_number: Optional[str] = Field(None, max_length=50)
    object: str = Field(..., min_length=1, max_length=500)
    procedure_type: ProcedureType
    contracting_authority: Optional[str] = Field(None, max_length=200)
    estimated_amount: Optional[float] = None
    currency: str = "MAD"
    publication_date: Optional[datetime] = None
    submission_deadline: datetime
    bid_opening_date: datetime
    bid_opening_time: Optional[str] = None
    submission_delay_days: Optional[int] = None
    status: PublicationStatus = PublicationStatus.DRAFT
    observations: Optional[str] = None


class PublicationCreate(PublicationBase):
    """Schéma pour la création d'une publication"""
    supports: List[PublicationSupportBase] = []


class PublicationUpdate(BaseModel):
    """Schéma pour la mise à jour d'une publication"""
    publication_number: Optional[str] = Field(None, max_length=50)
    notice_number: Optional[str] = Field(None, max_length=50)
    object: Optional[str] = Field(None, min_length=1, max_length=500)
    procedure_type: Optional[ProcedureType] = None
    contracting_authority: Optional[str] = Field(None, max_length=200)
    estimated_amount: Optional[float] = None
    currency: Optional[str] = None
    publication_date: Optional[datetime] = None
    submission_deadline: Optional[datetime] = None
    bid_opening_date: Optional[datetime] = None
    bid_opening_time: Optional[str] = None
    submission_delay_days: Optional[int] = None
    status: Optional[PublicationStatus] = None
    observations: Optional[str] = None


class PublicationResponse(PublicationBase):
    """Schéma de réponse pour une publication"""
    id: int
    attachments: Optional[list] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    # Relations
    supports: List[PublicationSupportResponse] = []
    deadlines: List[PublicationDeadlineResponse] = []
    alerts: List[PublicationAlertResponse] = []
    history: List[PublicationHistoryResponse] = []

    class Config:
        from_attributes = True


class PublicationListResponse(BaseModel):
    """Schéma de réponse pour la liste paginée"""
    items: List[PublicationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DeadlineUpdateRequest(BaseModel):
    """Schéma pour la mise à jour d'une échéance"""
    deadline_date: Optional[datetime] = None
    deadline_time: Optional[str] = None
    is_completed: Optional[bool] = None


class StatusUpdateRequest(BaseModel):
    """Schéma pour la mise à jour du statut"""
    status: PublicationStatus
