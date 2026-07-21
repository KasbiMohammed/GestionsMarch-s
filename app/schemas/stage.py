"""
Schémas pour la gestion des étapes des marchés
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.stage import StageStatus, StageCategory


class StageBase(BaseModel):
    """Base schema pour étape"""
    name: str = Field(..., min_length=2, max_length=200)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    category: Optional[StageCategory] = None
    order: Optional[int] = 0


class StageCreate(StageBase):
    """Schema pour la création d'étape"""
    market_id: int
    planned_date: Optional[datetime] = None
    responsible_id: Optional[int] = None
    checklist_items: Optional[str] = None
    documents_required: Optional[str] = None
    observations: Optional[str] = None


class StageUpdate(BaseModel):
    """Schema pour la mise à jour d'étape"""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    category: Optional[StageCategory] = None
    order: Optional[int] = None
    status: Optional[StageStatus] = None
    is_completed: Optional[bool] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    planned_date: Optional[datetime] = None
    actual_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    responsible_id: Optional[int] = None
    checklist_items: Optional[str] = None
    completed_checklist_items: Optional[str] = None
    documents_required: Optional[str] = None
    documents_provided: Optional[str] = None
    observations: Optional[str] = None
    comments: Optional[str] = None
    is_validated: Optional[bool] = None
    validation_notes: Optional[str] = None


class StageResponse(StageBase):
    """Schema pour la réponse étape"""
    id: int
    market_id: int
    status: StageStatus
    is_completed: bool
    progress_percentage: int
    planned_date: Optional[datetime] = None
    actual_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    responsible_id: Optional[int] = None
    checklist_items: Optional[str] = None
    completed_checklist_items: Optional[str] = None
    documents_required: Optional[str] = None
    documents_provided: Optional[str] = None
    observations: Optional[str] = None
    comments: Optional[str] = None
    is_validated: bool
    validated_by_id: Optional[int] = None
    validation_date: Optional[datetime] = None
    validation_notes: Optional[str] = None
    is_late: bool
    delay_days: int
    alert_level: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class StageBulkUpdate(BaseModel):
    """Schema pour la mise à jour en masse des étapes"""
    stage_ids: List[int]
    status: Optional[StageStatus] = None
    is_completed: Optional[bool] = None
    actual_date: Optional[datetime] = None
