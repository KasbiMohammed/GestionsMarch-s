"""
API de gestion de la préparation des marchés
Module 2: Préparation du dossier du marché
Endpoints CRUD avec validations, documents, historique et alertes
"""

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.auth.permissions import (
    can_create_planning,
    can_delete_planning,
    can_edit_planning,
    can_view_planning,
)
from app.database import get_db
from app.models.market_preparation import PreparationStatus
from app.models.user import User
from app.schemas.market_preparation import (
    MarketPreparationCreate,
    MarketPreparationListResponse,
    MarketPreparationResponse,
    MarketPreparationUpdate,
    PreparationDocumentResponse,
    PreparationHistoryResponse,
    PreparationAlertResponse,
    ValidationRequest,
    ValidationResponse,
)
from app.services.market_preparation_service import MarketPreparationService

router = APIRouter()


def get_market_preparation_service(db: Session) -> MarketPreparationService:
    """Dependency injection pour le service de préparation."""
    return MarketPreparationService(db)


@router.get("/", response_model=MarketPreparationListResponse)
async def list_preparations(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[PreparationStatus] = None,
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Liste paginée des préparations avec recherche, filtres et tri."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_market_preparation_service(db)
    items, total = service.list_preparations(
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return MarketPreparationListResponse(
        items=items,
        total=total,
        page=skip // limit + 1 if limit else 1,
        page_size=limit,
        total_pages=(total + limit - 1) // limit if limit else 1,
    )


@router.get("/{preparation_id}", response_model=MarketPreparationResponse)
async def get_preparation(
    preparation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Récupère une préparation par ID."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_market_preparation_service(db)
    preparation = service.get_preparation(preparation_id)
    
    if not preparation:
        raise HTTPException(status_code=404, detail="Préparation non trouvée")
    
    return preparation


@router.get("/planning/{planning_id}", response_model=MarketPreparationResponse)
async def get_preparation_by_planning(
    planning_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Récupère une préparation par ID de planification."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_market_preparation_service(db)
    preparation = service.get_preparation_by_planning(planning_id)
    
    if not preparation:
        raise HTTPException(status_code=404, detail="Préparation non trouvée")
    
    return preparation


@router.post("/", response_model=MarketPreparationResponse, status_code=status.HTTP_201_CREATED)
async def create_preparation(
    data: MarketPreparationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Crée un nouveau dossier de préparation à partir d'une planification validée."""
    if not can_create_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_market_preparation_service(db)
    
    try:
        preparation = service.create_preparation(
            planning_id=data.planning_id,
            data=data.dict(),
            user_id=current_user.id,
        )
        return preparation
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{preparation_id}", response_model=MarketPreparationResponse)
async def update_preparation(
    preparation_id: int,
    data: MarketPreparationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Met à jour une préparation."""
    if not can_edit_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_market_preparation_service(db)
    
    try:
        preparation = service.update_preparation(
            preparation_id=preparation_id,
            data=data.dict(exclude_unset=True),
            user_id=current_user.id,
        )
        return preparation
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{preparation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_preparation(
    preparation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Suppression logique d'une préparation."""
    if not can_delete_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_market_preparation_service(db)
    
    try:
        service.delete_preparation(
            preparation_id=preparation_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{preparation_id}/validate", response_model=ValidationResponse)
async def validate_preparation(
    preparation_id: int,
    validation: ValidationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Valide une préparation (technique, financière ou administrative)."""
    if not can_edit_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_market_preparation_service(db)
    
    try:
        preparation = service.validate_preparation(
            preparation_id=preparation_id,
            validation_type=validation.validation_type,
            approved=validation.approved,
            comments=validation.comments,
            user_id=current_user.id,
        )
        return ValidationResponse(
            success=True,
            message=f"Validation {validation.validation_type} {'approuvée' if validation.approved else 'rejetée'}",
            validation_date=preparation.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{preparation_id}/documents", response_model=list[PreparationDocumentResponse])
async def get_documents(
    preparation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Récupère les documents d'une préparation."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_market_preparation_service(db)
    preparation = service.get_preparation(preparation_id)
    
    if not preparation:
        raise HTTPException(status_code=404, detail="Préparation non trouvée")
    
    return preparation.documents


@router.post("/{preparation_id}/documents", response_model=PreparationDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    preparation_id: int,
    document_type: str = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Ajoute un document à la préparation."""
    if not can_edit_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_market_preparation_service(db)
    
    # TODO: Implémenter le stockage de fichier
    # Pour l'instant, utiliser un chemin temporaire
    file_path = f"uploads/preparations/{preparation_id}/{file.filename}"
    
    try:
        document = service.add_document(
            preparation_id=preparation_id,
            document_type=document_type,
            title=title,
            file_path=file_path,
            file_name=file.filename,
            file_size=file.size,
            file_type=file.content_type,
            user_id=current_user.id,
            description=description,
        )
        return document
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Supprime un document."""
    if not can_edit_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_market_preparation_service(db)
    
    try:
        service.delete_document(document_id=document_id, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{preparation_id}/history", response_model=list[PreparationHistoryResponse])
async def get_history(
    preparation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Récupère l'historique d'une préparation."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_market_preparation_service(db)
    history = service.get_history(preparation_id)
    return history


@router.get("/{preparation_id}/alerts", response_model=list[PreparationAlertResponse])
async def get_alerts(
    preparation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Récupère les alertes d'une préparation."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_market_preparation_service(db)
    alerts = service.get_alerts(preparation_id)
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

    service = get_market_preparation_service(db)
    
    try:
        service.resolve_alert(alert_id=alert_id, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/statistics/summary")
async def get_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Statistiques des préparations pour le tableau de bord."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_market_preparation_service(db)
    return service.get_statistics()
