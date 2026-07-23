"""
API de gestion du workflow de validation
Module 3: Validation administrative et technique
Endpoints CRUD avec décisions de validation, checklist, historique et alertes
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.auth.permissions import (
    can_create_planning,
    can_delete_planning,
    can_edit_planning,
    can_view_planning,
)
from app.database import get_db
from app.models.validation_workflow import ValidationStep, WorkflowStatus
from app.models.user import User
from app.schemas.validation_workflow import (
    ValidationWorkflowCreate,
    ValidationWorkflowListResponse,
    ValidationWorkflowResponse,
    ValidationWorkflowUpdate,
    ValidationRecordResponse,
    ValidationChecklistResponse,
    ValidationHistoryResponse,
    ValidationAlertResponse,
    ValidationDecisionRequest,
    ValidationDecisionResponse,
    ChecklistUpdateRequest,
)
from app.services.validation_workflow_service import ValidationWorkflowService

router = APIRouter()


def get_validation_workflow_service(db: Session) -> ValidationWorkflowService:
    """Dependency injection pour le service de workflow."""
    return ValidationWorkflowService(db)


@router.get("/", response_model=ValidationWorkflowListResponse)
async def list_workflows(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[WorkflowStatus] = None,
    current_step: Optional[ValidationStep] = None,
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Liste paginée des workflows avec recherche, filtres et tri."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_validation_workflow_service(db)
    items, total = service.list_workflows(
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        current_step=current_step,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return ValidationWorkflowListResponse(
        items=items,
        total=total,
        page=skip // limit + 1 if limit else 1,
        page_size=limit,
        total_pages=(total + limit - 1) // limit if limit else 1,
    )


@router.get("/{workflow_id}", response_model=ValidationWorkflowResponse)
async def get_workflow(
    workflow_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Récupère un workflow par ID."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_validation_workflow_service(db)
    workflow = service.get_workflow(workflow_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow non trouvé")
    
    return workflow


@router.get("/preparation/{preparation_id}", response_model=ValidationWorkflowResponse)
async def get_workflow_by_preparation(
    preparation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Récupère un workflow par ID de préparation."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_validation_workflow_service(db)
    workflow = service.get_workflow_by_preparation(preparation_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow non trouvé")
    
    return workflow


@router.post("/", response_model=ValidationWorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    data: ValidationWorkflowCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Crée un nouveau workflow de validation à partir d'une préparation."""
    if not can_create_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_validation_workflow_service(db)
    
    try:
        workflow = service.create_workflow(
            preparation_id=data.preparation_id,
            data=data.dict(),
            user_id=current_user.id,
        )
        return workflow
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{workflow_id}", response_model=ValidationWorkflowResponse)
async def update_workflow(
    workflow_id: int,
    data: ValidationWorkflowUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Met à jour un workflow."""
    if not can_edit_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_validation_workflow_service(db)
    
    try:
        workflow = service.update_workflow(
            workflow_id=workflow_id,
            data=data.dict(exclude_unset=True),
            user_id=current_user.id,
        )
        return workflow
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Suppression logique d'un workflow."""
    if not can_delete_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_validation_workflow_service(db)
    
    try:
        service.delete_workflow(
            workflow_id=workflow_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{workflow_id}/validate", response_model=ValidationDecisionResponse)
async def submit_validation_decision(
    workflow_id: int,
    decision: ValidationDecisionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Soumet une décision de validation pour une étape."""
    if not can_edit_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_validation_workflow_service(db)
    
    try:
        workflow = service.submit_validation_decision(
            workflow_id=workflow_id,
            step=decision.step,
            decision=decision.decision,
            observations=decision.observations,
            comments=decision.comments,
            return_step=decision.return_step,
            return_reason=decision.return_reason,
            user_id=current_user.id,
            user_name=current_user.full_name,
            user_role=str(current_user.role),
        )
        
        next_step = service.get_next_step(decision.step)
        
        return ValidationDecisionResponse(
            success=True,
            message=f"Validation {decision.step.value}: {decision.decision.value}",
            next_step=next_step,
            validation_date=workflow.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{workflow_id}/checklist", response_model=ValidationChecklistResponse)
async def get_checklist(
    workflow_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Récupère la checklist de conformité d'un workflow."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_validation_workflow_service(db)
    workflow = service.get_workflow(workflow_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow non trouvé")
    
    return workflow.checklist


@router.put("/{workflow_id}/checklist", response_model=ValidationChecklistResponse)
async def update_checklist(
    workflow_id: int,
    data: ChecklistUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Met à jour la checklist de conformité."""
    if not can_edit_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_validation_workflow_service(db)
    
    try:
        checklist = service.update_checklist(
            workflow_id=workflow_id,
            data=data.dict(),
            user_id=current_user.id,
        )
        return checklist
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{workflow_id}/history", response_model=list[ValidationHistoryResponse])
async def get_history(
    workflow_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Récupère l'historique d'un workflow."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_validation_workflow_service(db)
    history = service.get_history(workflow_id)
    return history


@router.get("/{workflow_id}/alerts", response_model=list[ValidationAlertResponse])
async def get_alerts(
    workflow_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Récupère les alertes d'un workflow."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_validation_workflow_service(db)
    alerts = service.get_alerts(workflow_id)
    return alerts


@router.post("/alerts/{alert_id}/resolve", status_code=status.HTTP_204_NO_CONTENT)
async def resolve_alert(
    alert_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Résout une alerte."""
    if not can_edit_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_validation_workflow_service(db)
    
    try:
        service.resolve_alert(alert_id=alert_id, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/statistics/summary")
async def get_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Statistiques des workflows pour le tableau de bord."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_validation_workflow_service(db)
    return service.get_statistics()
