"""
Schémas Pydantic pour la planification des marchés
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.market_planning import (
    ProjectType,
    ProcedureType,
    PlanningPriority,
    MarketPlanningStatus,
)


class PlanningDocumentBase(BaseModel):
    """Schéma de base pour un document de planification"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class PlanningDocumentResponse(PlanningDocumentBase):
    """Schéma de réponse pour un document"""
    id: int
    planning_id: int
    file_name: str
    file_path: str
    file_size: Optional[float] = None
    file_type: Optional[str] = None
    uploaded_by: Optional[int] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class MarketPlanningBase(BaseModel):
    """Schéma de base pour une planification"""
    planning_number: str = Field(..., min_length=1, max_length=50)
    fiscal_year: int = Field(..., ge=2000, le=2100)
    title: str = Field(..., min_length=3, max_length=300)
    description: Optional[str] = None
    project_type: ProjectType
    procedure_type: ProcedureType
    estimated_budget: float = Field(..., ge=0)
    funding_source: Optional[str] = Field(None, max_length=200)
    requesting_service_id: Optional[int] = None
    requesting_service_name: Optional[str] = Field(None, max_length=200)
    responsible_id: Optional[int] = None
    responsible_name: Optional[str] = Field(None, max_length=200)
    priority: PlanningPriority = PlanningPriority.MOYENNE
    status: MarketPlanningStatus = MarketPlanningStatus.BROUILLON
    launch_date: Optional[datetime] = None
    bid_opening_date: Optional[datetime] = None
    attribution_date: Optional[datetime] = None
    notification_date: Optional[datetime] = None
    service_order_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    observations: Optional[str] = None


class MarketPlanningCreate(MarketPlanningBase):
    """Schéma pour la création d'une planification"""
    pass


class MarketPlanningUpdate(BaseModel):
    """Schéma pour la mise à jour d'une planification"""
    planning_number: Optional[str] = Field(None, min_length=1, max_length=50)
    fiscal_year: Optional[int] = Field(None, ge=2000, le=2100)
    title: Optional[str] = Field(None, min_length=3, max_length=300)
    description: Optional[str] = None
    project_type: Optional[ProjectType] = None
    procedure_type: Optional[ProcedureType] = None
    estimated_budget: Optional[float] = Field(None, ge=0)
    funding_source: Optional[str] = Field(None, max_length=200)
    requesting_service_id: Optional[int] = None
    requesting_service_name: Optional[str] = Field(None, max_length=200)
    responsible_id: Optional[int] = None
    responsible_name: Optional[str] = Field(None, max_length=200)
    priority: Optional[PlanningPriority] = None
    status: Optional[MarketPlanningStatus] = None
    launch_date: Optional[datetime] = None
    bid_opening_date: Optional[datetime] = None
    attribution_date: Optional[datetime] = None
    notification_date: Optional[datetime] = None
    service_order_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    observations: Optional[str] = None


class MarketPlanningResponse(MarketPlanningBase):
    """Schéma de réponse pour une planification"""
    id: int
    created_by: Optional[int] = None
    modified_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    documents: List[PlanningDocumentResponse] = []

    class Config:
        from_attributes = True


class MarketPlanningListResponse(BaseModel):
    """Schéma de réponse pour la liste paginée"""
    items: List[MarketPlanningResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class MarketPlanningStatistics(BaseModel):
    """Statistiques de planification pour le tableau de bord"""
    total_count: int
    total_budget: float
    by_project_type: dict
    by_procedure_type: dict
    by_status: dict
