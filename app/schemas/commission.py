"""
Schémas Pydantic pour la gestion des commissions
Module 4: Constitution et gestion de la commission
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.commission import (
    CommissionStatus,
    SessionStatus,
    MemberRole,
)


class CommissionMemberBase(BaseModel):
    """Schéma de base pour un membre de commission"""
    user_id: int = Field(..., gt=0)
    role: MemberRole
    is_president: bool = False
    is_secretary: bool = False
    user_name: Optional[str] = None
    user_function: Optional[str] = None
    user_department: Optional[str] = None
    substitute_for_id: Optional[int] = None


class CommissionMemberResponse(CommissionMemberBase):
    """Schéma de réponse pour un membre de commission"""
    id: int
    commission_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CommissionSessionBase(BaseModel):
    """Schéma de base pour une séance de commission"""
    session_number: int = Field(..., gt=0)
    session_title: str = Field(..., min_length=1, max_length=200)
    session_type: Optional[str] = None
    planned_date: datetime
    planned_time: Optional[str] = None
    location: Optional[str] = None
    agenda: Optional[str] = None
    observations: Optional[str] = None
    decisions: Optional[str] = None


class CommissionSessionResponse(CommissionSessionBase):
    """Schéma de réponse pour une séance de commission"""
    id: int
    commission_id: int
    status: SessionStatus
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    members_present: Optional[list] = None
    members_absent: Optional[list] = None
    pv_content: Optional[str] = None
    pv_generated: bool = False
    pv_generated_by: Optional[int] = None
    pv_generated_at: Optional[datetime] = None
    pv_attachment_path: Optional[str] = None
    pv_attachment_name: Optional[str] = None
    attachments: Optional[list] = None
    postponed_to: Optional[datetime] = None
    postponed_reason: Optional[str] = None
    suspended_reason: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_by: Optional[int] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CommissionAlertBase(BaseModel):
    """Schéma de base pour une alerte de commission"""
    alert_type: str = Field(..., min_length=1, max_length=50)
    severity: str = Field(..., min_length=1, max_length=20)
    title: str = Field(..., min_length=1, max_length=200)
    message: Optional[str] = None
    session_id: Optional[int] = None


class CommissionAlertResponse(CommissionAlertBase):
    """Schéma de réponse pour une alerte de commission"""
    id: int
    commission_id: int
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CommissionHistoryBase(BaseModel):
    """Schéma de base pour l'historique de commission"""
    action: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    session_id: Optional[int] = None
    member_id: Optional[int] = None


class CommissionHistoryResponse(CommissionHistoryBase):
    """Schéma de réponse pour l'historique de commission"""
    id: int
    commission_id: int
    user_id: int
    user_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CommissionBase(BaseModel):
    """Schéma de base pour une commission"""
    workflow_id: int = Field(..., gt=0)
    commission_number: Optional[str] = Field(None, max_length=50)
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: CommissionStatus = CommissionStatus.TO_BE_CONSTITUTED
    observations: Optional[str] = None


class CommissionCreate(CommissionBase):
    """Schéma pour la création d'une commission"""
    members: List[CommissionMemberBase] = []


class CommissionUpdate(BaseModel):
    """Schéma pour la mise à jour d'une commission"""
    commission_number: Optional[str] = Field(None, max_length=50)
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[CommissionStatus] = None
    observations: Optional[str] = None


class CommissionResponse(CommissionBase):
    """Schéma de réponse pour une commission"""
    id: int
    constituted_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    # Relations
    members: List[CommissionMemberResponse] = []
    sessions: List[CommissionSessionResponse] = []
    alerts: List[CommissionAlertResponse] = []
    history: List[CommissionHistoryResponse] = []

    class Config:
        from_attributes = True


class CommissionListResponse(BaseModel):
    """Schéma de réponse pour la liste paginée"""
    items: List[CommissionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SessionUpdateRequest(BaseModel):
    """Schéma pour la mise à jour d'une séance"""
    session_title: Optional[str] = Field(None, min_length=1, max_length=200)
    session_type: Optional[str] = None
    planned_date: Optional[datetime] = None
    planned_time: Optional[str] = None
    location: Optional[str] = None
    agenda: Optional[str] = None
    observations: Optional[str] = None
    decisions: Optional[str] = None
    members_present: Optional[list] = None
    members_absent: Optional[list] = None


class SessionStatusUpdateRequest(BaseModel):
    """Schéma pour la mise à jour du statut d'une séance"""
    status: SessionStatus
    postponed_to: Optional[datetime] = None
    postponed_reason: Optional[str] = None
    suspended_reason: Optional[str] = None


class PVGenerationRequest(BaseModel):
    """Schéma pour la génération d'un PV"""
    pv_content: str
