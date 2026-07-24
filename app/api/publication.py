"""
API de gestion des publications
Module 5: Publication de l'avis et lancement de la consultation
Endpoints CRUD avec supports, échéances et alertes
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
from app.models.publication import PublicationStatus
from app.models.user import User
from app.schemas.publication import (
    PublicationCreate,
    PublicationListResponse,
    PublicationResponse,
    PublicationUpdate,
    PublicationSupportBase,
    PublicationSupportResponse,
    PublicationDeadlineBase,
    PublicationDeadlineResponse,
    DeadlineUpdateRequest,
    StatusUpdateRequest,
    PublicationAlertResponse,
    PublicationHistoryResponse,
)
from app.services.publication_service import PublicationService

router = APIRouter()


def get_publication_service(db: Session) -> PublicationService:
    """Dependency injection pour le service de publication."""
    return PublicationService(db)


@router.get("/", response_model=PublicationListResponse)
async def list_publications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[PublicationStatus] = None,
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Liste paginée des publications avec recherche, filtres et tri."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_publication_service(db)
    items, total = service.list_publications(
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return PublicationListResponse(
        items=items,
        total=total,
        page=skip // limit + 1 if limit else 1,
        page_size=limit,
        total_pages=(total + limit - 1) // limit if limit else 1,
    )


@router.get("/{publication_id}", response_model=PublicationResponse)
async def get_publication(
    publication_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Récupère une publication par ID."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_publication_service(db)
    publication = service.get_publication(publication_id)
    
    if not publication:
        raise HTTPException(status_code=404, detail="Publication non trouvée")
    
    return publication


@router.get("/commission/{commission_id}", response_model=list[PublicationResponse])
async def get_publications_by_commission(
    commission_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Récupère toutes les publications d'une commission."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_publication_service(db)
    publications = service.get_publications_by_commission(commission_id)
    return publications


@router.post("/", response_model=PublicationResponse, status_code=status.HTTP_201_CREATED)
async def create_publication(
    data: PublicationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Crée une nouvelle publication à partir d'une commission clôturée."""
    if not can_create_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_publication_service(db)
    
    try:
        publication = service.create_publication(
            commission_id=data.commission_id,
            data=data.dict(),
            user_id=current_user.id,
        )
        return publication
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{publication_id}", response_model=PublicationResponse)
async def update_publication(
    publication_id: int,
    data: PublicationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Met à jour une publication."""
    if not can_edit_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_publication_service(db)
    
    try:
        publication = service.update_publication(
            publication_id=publication_id,
            data=data.dict(exclude_unset=True),
            user_id=current_user.id,
        )
        return publication
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{publication_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_publication(
    publication_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Suppression logique d'une publication."""
    if not can_delete_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_publication_service(db)
    
    try:
        service.delete_publication(
            publication_id=publication_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{publication_id}/supports", response_model=PublicationSupportResponse, status_code=status.HTTP_201_CREATED)
async def add_support(
    publication_id: int,
    data: PublicationSupportBase,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Ajoute un support de publication."""
    if not can_edit_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_publication_service(db)
    
    try:
        support = service.add_support(
            publication_id=publication_id,
            data=data.dict(),
            user_id=current_user.id,
        )
        return support
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/deadlines/{deadline_id}", response_model=PublicationDeadlineResponse)
async def update_deadline(
    deadline_id: int,
    data: DeadlineUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Met à jour une échéance."""
    if not can_edit_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_publication_service(db)
    
    try:
        deadline = service.update_deadline(
            deadline_id=deadline_id,
            data=data.dict(exclude_unset=True),
            user_id=current_user.id,
        )
        return deadline
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{publication_id}/status", response_model=PublicationResponse)
async def update_status(
    publication_id: int,
    data: StatusUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Met à jour le statut d'une publication."""
    if not can_edit_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_publication_service(db)
    
    try:
        publication = service.update_status(
            publication_id=publication_id,
            status=data.status,
            user_id=current_user.id,
        )
        return publication
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{publication_id}/history", response_model=list[PublicationHistoryResponse])
async def get_history(
    publication_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Récupère l'historique d'une publication."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_publication_service(db)
    history = service.get_history(publication_id)
    return history


@router.get("/{publication_id}/alerts", response_model=list[PublicationAlertResponse])
async def get_alerts(
    publication_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Récupère les alertes d'une publication."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_publication_service(db)
    alerts = service.get_alerts(publication_id)
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

    service = get_publication_service(db)
    
    try:
        service.resolve_alert(alert_id=alert_id, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/statistics/summary")
async def get_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Statistiques des publications pour le tableau de bord."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_publication_service(db)
    return service.get_statistics()
