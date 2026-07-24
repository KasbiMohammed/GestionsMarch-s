"""
API de gestion des commissions
Module 4: Constitution et gestion de la commission
Endpoints CRUD avec membres, séances, PV et alertes
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
from app.models.commission import CommissionStatus, SessionStatus
from app.models.user import User
from app.schemas.commission import (
    CommissionCreate,
    CommissionListResponse,
    CommissionResponse,
    CommissionUpdate,
    CommissionMemberBase,
    CommissionMemberResponse,
    CommissionSessionBase,
    CommissionSessionResponse,
    SessionUpdateRequest,
    SessionStatusUpdateRequest,
    PVGenerationRequest,
    CommissionAlertResponse,
    CommissionHistoryResponse,
)
from app.services.commission_service import CommissionService

router = APIRouter()


def get_commission_service(db: Session) -> CommissionService:
    """Dependency injection pour le service de commission."""
    return CommissionService(db)


@router.get("/", response_model=CommissionListResponse)
async def list_commissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[CommissionStatus] = None,
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Liste paginée des commissions avec recherche, filtres et tri."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_commission_service(db)
    items, total = service.list_commissions(
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return CommissionListResponse(
        items=items,
        total=total,
        page=skip // limit + 1 if limit else 1,
        page_size=limit,
        total_pages=(total + limit - 1) // limit if limit else 1,
    )


@router.get("/{commission_id}", response_model=CommissionResponse)
async def get_commission(
    commission_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Récupère une commission par ID."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_commission_service(db)
    commission = service.get_commission(commission_id)
    
    if not commission:
        raise HTTPException(status_code=404, detail="Commission non trouvée")
    
    return commission


@router.get("/workflow/{workflow_id}", response_model=CommissionResponse)
async def get_commission_by_workflow(
    workflow_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Récupère une commission par ID de workflow."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_commission_service(db)
    commission = service.get_commission_by_workflow(workflow_id)
    
    if not commission:
        raise HTTPException(status_code=404, detail="Commission non trouvée")
    
    return commission


@router.post("/", response_model=CommissionResponse, status_code=status.HTTP_201_CREATED)
async def create_commission(
    data: CommissionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Crée une nouvelle commission à partir d'un workflow validé."""
    if not can_create_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_commission_service(db)
    
    try:
        commission = service.create_commission(
            workflow_id=data.workflow_id,
            data=data.dict(),
            user_id=current_user.id,
        )
        return commission
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{commission_id}", response_model=CommissionResponse)
async def update_commission(
    commission_id: int,
    data: CommissionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Met à jour une commission."""
    if not can_edit_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_commission_service(db)
    
    try:
        commission = service.update_commission(
            commission_id=commission_id,
            data=data.dict(exclude_unset=True),
            user_id=current_user.id,
        )
        return commission
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{commission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_commission(
    commission_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Suppression logique d'une commission."""
    if not can_delete_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_commission_service(db)
    
    try:
        service.delete_commission(
            commission_id=commission_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{commission_id}/members", response_model=CommissionMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_member(
    commission_id: int,
    data: CommissionMemberBase,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Ajoute un membre à la commission."""
    if not can_edit_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_commission_service(db)
    
    try:
        member = service.add_member(
            commission_id=commission_id,
            data=data.dict(),
            user_id=current_user.id,
        )
        return member
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    member_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Supprime un membre de la commission."""
    if not can_edit_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_commission_service(db)
    
    try:
        service.remove_member(member_id=member_id, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{commission_id}/sessions", response_model=CommissionSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    commission_id: int,
    data: CommissionSessionBase,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Crée une nouvelle séance pour la commission."""
    if not can_edit_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_commission_service(db)
    
    try:
        session = service.create_session(
            commission_id=commission_id,
            data=data.dict(),
            user_id=current_user.id,
        )
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/sessions/{session_id}", response_model=CommissionSessionResponse)
async def update_session(
    session_id: int,
    data: SessionUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Met à jour une séance."""
    if not can_edit_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_commission_service(db)
    
    try:
        session = service.update_session(
            session_id=session_id,
            data=data.dict(exclude_unset=True),
            user_id=current_user.id,
        )
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/sessions/{session_id}/status", response_model=CommissionSessionResponse)
async def update_session_status(
    session_id: int,
    data: SessionStatusUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Met à jour le statut d'une séance."""
    if not can_edit_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_commission_service(db)
    
    try:
        session = service.update_session_status(
            session_id=session_id,
            status=data.status,
            user_id=current_user.id,
            postponed_to=data.postponed_to,
            postponed_reason=data.postponed_reason,
            suspended_reason=data.suspended_reason,
        )
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions/{session_id}/pv", response_model=CommissionSessionResponse)
async def generate_pv(
    session_id: int,
    data: PVGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Génère le procès-verbal d'une séance."""
    if not can_edit_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_commission_service(db)
    
    try:
        session = service.generate_pv(
            session_id=session_id,
            pv_content=data.pv_content,
            user_id=current_user.id,
        )
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{commission_id}/close", response_model=CommissionResponse)
async def close_commission(
    commission_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Clôture la commission."""
    if not can_edit_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_commission_service(db)
    
    try:
        commission = service.close_commission(
            commission_id=commission_id,
            user_id=current_user.id,
        )
        return commission
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{commission_id}/history", response_model=list[CommissionHistoryResponse])
async def get_history(
    commission_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Récupère l'historique d'une commission."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_commission_service(db)
    history = service.get_history(commission_id)
    return history


@router.get("/{commission_id}/alerts", response_model=list[CommissionAlertResponse])
async def get_alerts(
    commission_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Récupère les alertes d'une commission."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_commission_service(db)
    alerts = service.get_alerts(commission_id)
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

    service = get_commission_service(db)
    
    try:
        service.resolve_alert(alert_id=alert_id, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/statistics/summary")
async def get_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Statistiques des commissions pour le tableau de bord."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_commission_service(db)
    return service.get_statistics()
