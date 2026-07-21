"""
Schémas pour la gestion des documents
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.document import DocumentType, DocumentCategory


class DocumentBase(BaseModel):
    """Base schema pour document"""
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    document_type: Optional[DocumentType] = None
    category: Optional[DocumentCategory] = None


class DocumentCreate(DocumentBase):
    """Schema pour la création de document"""
    market_id: int
    stage_id: Optional[int] = None
    observations: Optional[str] = None


class DocumentUpdate(BaseModel):
    """Schema pour la mise à jour de document"""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    document_type: Optional[DocumentType] = None
    category: Optional[DocumentCategory] = None
    is_validated: Optional[bool] = None
    validation_notes: Optional[str] = None
    observations: Optional[str] = None


class DocumentResponse(DocumentBase):
    """Schema pour la réponse document"""
    id: int
    market_id: int
    stage_id: Optional[int] = None
    file_name: str
    file_path: str
    file_size: Optional[float] = None
    file_type: Optional[str] = None
    file_hash: Optional[str] = None
    version: int
    is_current_version: bool
    previous_version_id: Optional[int] = None
    upload_date: datetime
    uploaded_by: Optional[int] = None
    is_validated: bool
    validated_by: Optional[int] = None
    validation_date: Optional[datetime] = None
    observations: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
