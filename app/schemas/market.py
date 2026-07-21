"""
Schémas pour la gestion des marchés publics
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.market import MarketType, ProcurementMethod, MarketStatus


class CompanyBase(BaseModel):
    """Base schema pour entreprise"""
    name: str = Field(..., min_length=2, max_length=200)
    rc_number: Optional[str] = None
    if_number: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class CompanyCreate(CompanyBase):
    """Schema pour la création d'entreprise"""
    offer_amount: Optional[float] = None
    observations: Optional[str] = None


class CompanyUpdate(BaseModel):
    """Schema pour la mise à jour d'entreprise"""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    rc_number: Optional[str] = None
    if_number: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    offer_amount: Optional[float] = None
    is_attributed: Optional[bool] = None
    is_abnormally_low: Optional[bool] = None
    is_abnormally_high: Optional[bool] = None
    technical_score: Optional[float] = None
    financial_score: Optional[float] = None
    total_score: Optional[float] = None
    observations: Optional[str] = None


class CompanyResponse(CompanyBase):
    """Schema pour la réponse entreprise"""
    id: int
    market_id: int
    offer_amount: Optional[float] = None
    offer_rank: Optional[int] = None
    is_attributed: bool
    is_abnormally_low: bool
    is_abnormally_high: bool
    technical_score: Optional[float] = None
    financial_score: Optional[float] = None
    total_score: Optional[float] = None
    observations: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MarketBase(BaseModel):
    """Base schema pour marché"""
    market_number: str = Field(..., min_length=1, max_length=50)
    object: str = Field(..., min_length=5)
    master_of_work: str = Field(..., min_length=2, max_length=200)
    market_type: MarketType
    procurement_method: ProcurementMethod
    estimated_amount: float = Field(..., gt=0)
    budget: Optional[float] = None
    credits: Optional[float] = None
    responsible_service: Optional[str] = None
    follow_up_responsible: Optional[str] = None


class MarketCreate(MarketBase):
    """Schema pour la création de marché"""
    definitive_amount: Optional[float] = None
    publication_date: Optional[datetime] = None
    opening_date: Optional[datetime] = None
    attribution_date: Optional[datetime] = None
    notification_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    expected_end_date: Optional[datetime] = None
    observations: Optional[str] = None
    comments: Optional[str] = None
    companies: Optional[List[CompanyCreate]] = None


class MarketUpdate(BaseModel):
    """Schema pour la mise à jour de marché"""
    market_number: Optional[str] = Field(None, min_length=1, max_length=50)
    object: Optional[str] = Field(None, min_length=5)
    master_of_work: Optional[str] = Field(None, min_length=2, max_length=200)
    market_type: Optional[MarketType] = None
    procurement_method: Optional[ProcurementMethod] = None
    estimated_amount: Optional[float] = Field(None, gt=0)
    definitive_amount: Optional[float] = None
    budget: Optional[float] = None
    credits: Optional[float] = None
    responsible_service: Optional[str] = None
    follow_up_responsible: Optional[str] = None
    publication_date: Optional[datetime] = None
    opening_date: Optional[datetime] = None
    attribution_date: Optional[datetime] = None
    notification_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    expected_end_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    provisional_acceptance_date: Optional[datetime] = None
    definitive_acceptance_date: Optional[datetime] = None
    status: Optional[MarketStatus] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    observations: Optional[str] = None
    comments: Optional[str] = None


class MarketResponse(MarketBase):
    """Schema pour la réponse marché"""
    id: int
    definitive_amount: Optional[float] = None
    budget: Optional[float] = None
    credits: Optional[float] = None
    responsible_service: Optional[str] = None
    follow_up_responsible: Optional[str] = None
    publication_date: Optional[datetime] = None
    opening_date: Optional[datetime] = None
    attribution_date: Optional[datetime] = None
    notification_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    expected_end_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    provisional_acceptance_date: Optional[datetime] = None
    definitive_acceptance_date: Optional[datetime] = None
    status: MarketStatus
    progress_percentage: int
    participating_companies_count: int
    observations: Optional[str] = None
    comments: Optional[str] = None
    created_by: Optional[int] = None
    modified_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    companies: List[CompanyResponse] = []
    
    class Config:
        from_attributes = True


class MarketListResponse(BaseModel):
    """Schema pour la liste des marchés avec pagination"""
    items: List[MarketResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
