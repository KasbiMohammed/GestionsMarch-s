"""
API de gestion des étapes des marchés
Endpoints pour la gestion des étapes et check-lists
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.stage import Stage, StageStatus
from app.schemas.stage import StageCreate, StageUpdate, StageResponse, StageBulkUpdate
from app.auth.dependencies import get_current_active_user

router = APIRouter()


@router.get("/market/{market_id}", response_model=List[StageResponse])
async def get_market_stages(
    market_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupère toutes les étapes d'un marché
    
    Args:
        market_id: ID du marché
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Liste des étapes du marché
    """
    stages = db.query(Stage).filter(Stage.market_id == market_id).order_by(Stage.order).all()
    return stages


@router.get("/{stage_id}", response_model=StageResponse)
async def get_stage(
    stage_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupère une étape par son ID
    
    Args:
        stage_id: ID de l'étape
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Étape demandée
        
    Raises:
        HTTPException: Si l'étape n'existe pas
    """
    stage = db.query(Stage).filter(Stage.id == stage_id).first()
    
    if not stage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stage not found"
        )
    
    return stage


@router.post("/", response_model=StageResponse, status_code=status.HTTP_201_CREATED)
async def create_stage(
    stage_data: StageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Crée une nouvelle étape
    
    Args:
        stage_data: Données de l'étape
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Étape créée
    """
    from app.models.market import Market
    
    # Vérifier si le marché existe
    market = db.query(Market).filter(Market.id == stage_data.market_id).first()
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )
    
    # Créer l'étape
    db_stage = Stage(**stage_data.model_dump())
    db.add(db_stage)
    db.commit()
    db.refresh(db_stage)
    
    return db_stage


@router.put("/{stage_id}", response_model=StageResponse)
async def update_stage(
    stage_id: int,
    stage_update: StageUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Met à jour une étape
    
    Args:
        stage_id: ID de l'étape
        stage_update: Données de mise à jour
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Étape mise à jour
        
    Raises:
        HTTPException: Si l'étape n'existe pas
    """
    stage = db.query(Stage).filter(Stage.id == stage_id).first()
    
    if not stage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stage not found"
        )
    
    # Mise à jour des champs
    update_data = stage_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(stage, field, value)
    
    # Calculer le retard si les dates sont fournies
    if 'planned_date' in update_data or 'actual_date' in update_data:
        stage.calculate_delay()
    
    db.commit()
    db.refresh(stage)
    
    return stage


@router.post("/bulk-update", response_model=List[StageResponse])
async def bulk_update_stages(
    bulk_update: StageBulkUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Met à jour plusieurs étapes en une seule requête
    
    Args:
        bulk_update: Données de mise à jour en masse
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Liste des étapes mises à jour
    """
    stages = db.query(Stage).filter(Stage.id.in_(bulk_update.stage_ids)).all()
    
    if not stages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No stages found"
        )
    
    update_data = bulk_update.model_dump(exclude={'stage_ids'}, exclude_unset=True)
    
    for stage in stages:
        for field, value in update_data.items():
            setattr(stage, field, value)
        
        # Calculer le retard
        stage.calculate_delay()
    
    db.commit()
    
    # Rafraîchir les étapes
    for stage in stages:
        db.refresh(stage)
    
    return stages


@router.delete("/{stage_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stage(
    stage_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Supprime une étape
    
    Args:
        stage_id: ID de l'étape
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Raises:
        HTTPException: Si l'étape n'existe pas
    """
    stage = db.query(Stage).filter(Stage.id == stage_id).first()
    
    if not stage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stage not found"
        )
    
    db.delete(stage)
    db.commit()
    
    return None


@router.post("/{stage_id}/validate", response_model=StageResponse)
async def validate_stage(
    stage_id: int,
    validation_notes: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Valide une étape
    
    Args:
        stage_id: ID de l'étape
        validation_notes: Notes de validation
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Étape validée
    """
    from datetime import datetime
    
    stage = db.query(Stage).filter(Stage.id == stage_id).first()
    
    if not stage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stage not found"
        )
    
    stage.is_validated = True
    stage.validated_by_id = current_user.id
    stage.validation_date = datetime.utcnow()
    stage.validation_notes = validation_notes
    
    db.commit()
    db.refresh(stage)
    
    return stage
