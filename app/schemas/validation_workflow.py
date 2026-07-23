"""
Schémas Pydantic pour le workflow de validation
Module 3: Validation administrative et technique
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.validation_workflow import (
    ValidationStep,
    ValidationDecision,
    WorkflowStatus,
)


class ValidationRecordBase(BaseModel):
    """Schéma de base pour un enregistrement de validation"""
    step: ValidationStep
    decision: ValidationDecision = ValidationDecision.PENDING
    observations: Optional[str] = None
    comments: Optional[str] = None
    return_step: Optional[ValidationStep] = None
    return_reason: Optional[str] = None


class ValidationRecordResponse(ValidationRecordBase):
    """Schéma de réponse pour un enregistrement de validation"""
    id: int
    workflow_id: int
    validator_id: Optional[int] = None
    validator_name: Optional[str] = None
    validator_role: Optional[str] = None
    validated_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    attachment_path: Optional[str] = None
    attachment_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ValidationChecklistBase(BaseModel):
    """Schéma de base pour la checklist de conformité"""
    documents_complete: bool = False
    documents_observations: Optional[str] = None
    budget_valid: bool = False
    budget_observations: Optional[str] = None
    estimates_valid: bool = False
    estimates_observations: Optional[str] = None
    signatures_valid: bool = False
    signatures_observations: Optional[str] = None
    information_coherent: bool = False
    information_observations: Optional[str] = None
    regulatory_compliance: bool = False
    regulatory_observations: Optional[str] = None


class ValidationChecklistResponse(ValidationChecklistBase):
    """Schéma de réponse pour la checklist"""
    id: int
    workflow_id: int
    additional_criteria: Optional[dict] = None
    calculated_percentage: int = 0
    checked_by: Optional[int] = None
    checked_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ValidationHistoryBase(BaseModel):
    """Schéma de base pour l'historique de validation"""
    action: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    from_step: Optional[ValidationStep] = None
    to_step: Optional[ValidationStep] = None
    decision: Optional[ValidationDecision] = None


class ValidationHistoryResponse(ValidationHistoryBase):
    """Schéma de réponse pour l'historique"""
    id: int
    workflow_id: int
    user_id: int
    user_name: Optional[str] = None
    user_role: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ValidationAlertBase(BaseModel):
    """Schéma de base pour une alerte de validation"""
    alert_type: str = Field(..., min_length=1, max_length=50)
    severity: str = Field(..., min_length=1, max_length=20)
    title: str = Field(..., min_length=1, max_length=200)
    message: Optional[str] = None
    step: Optional[ValidationStep] = None


class ValidationAlertResponse(ValidationAlertBase):
    """Schéma de réponse pour une alerte"""
    id: int
    workflow_id: int
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ValidationWorkflowBase(BaseModel):
    """Schéma de base pour un workflow de validation"""
    preparation_id: int = Field(..., gt=0)
    workflow_number: Optional[str] = Field(None, max_length=50)
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step: ValidationStep = ValidationStep.REQUESTING_SERVICE
    global_observations: Optional[str] = None


class ValidationWorkflowCreate(ValidationWorkflowBase):
    """Schéma pour la création d'un workflow"""
    pass


class ValidationWorkflowUpdate(BaseModel):
    """Schéma pour la mise à jour d'un workflow"""
    workflow_number: Optional[str] = Field(None, max_length=50)
    status: Optional[WorkflowStatus] = None
    current_step: Optional[ValidationStep] = None
    global_observations: Optional[str] = None


class ValidationWorkflowResponse(ValidationWorkflowBase):
    """Schéma de réponse pour un workflow"""
    id: int
    conformity_percentage: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    # Relations
    validations: List[ValidationRecordResponse] = []
    checklist: Optional[ValidationChecklistResponse] = None
    history: List[ValidationHistoryResponse] = []
    alerts: List[ValidationAlertResponse] = []

    class Config:
        from_attributes = True


class ValidationWorkflowListResponse(BaseModel):
    """Schéma de réponse pour la liste paginée"""
    items: List[ValidationWorkflowResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ValidationDecisionRequest(BaseModel):
    """Schéma pour une décision de validation"""
    step: ValidationStep
    decision: ValidationDecision
    observations: Optional[str] = None
    comments: Optional[str] = None
    return_step: Optional[ValidationStep] = None
    return_reason: Optional[str] = None


class ValidationDecisionResponse(BaseModel):
    """Schéma de réponse pour une décision de validation"""
    success: bool
    message: str
    next_step: Optional[ValidationStep] = None
    validation_date: Optional[datetime] = None


class ChecklistUpdateRequest(BaseModel):
    """Schéma pour la mise à jour de la checklist"""
    documents_complete: bool = False
    documents_observations: Optional[str] = None
    budget_valid: bool = False
    budget_observations: Optional[str] = None
    estimates_valid: bool = False
    estimates_observations: Optional[str] = None
    signatures_valid: bool = False
    signatures_observations: Optional[str] = None
    information_coherent: bool = False
    information_observations: Optional[str] = None
    regulatory_compliance: bool = False
    regulatory_observations: Optional[str] = None
