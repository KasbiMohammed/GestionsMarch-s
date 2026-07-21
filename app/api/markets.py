"""
API de gestion des marchés publics
Endpoints pour la gestion CRUD des marchés
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.market import Market, MarketStatus
from app.schemas.market import MarketCreate, MarketUpdate, MarketResponse, MarketListResponse, CompanyCreate, CompanyResponse
from app.auth.dependencies import get_current_active_user
from app.auth.permissions import can_create_market, can_edit_market, can_delete_market

router = APIRouter()


@router.get("/", response_model=MarketListResponse)
async def get_markets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[MarketStatus] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupère la liste des marchés avec pagination et filtres
    
    Args:
        skip: Nombre de marchés à sauter
        limit: Nombre maximum de marchés à retourner
        status: Filtrer par statut
        search: Recherche par numéro ou objet
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Liste paginée des marchés
    """
    query = db.query(Market)
    
    # Filtrage par statut
    if status:
        query = query.filter(Market.status == status)
    
    # Recherche textuelle
    if search:
        query = query.filter(
            (Market.market_number.ilike(f"%{search}%")) |
            (Market.object.ilike(f"%{search}%"))
        )
    
    # Pagination
    total = query.count()
    markets = query.order_by(Market.created_at.desc()).offset(skip).limit(limit).all()
    
    return MarketListResponse(
        items=markets,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        total_pages=(total + limit - 1) // limit
    )


@router.get("/{market_id}", response_model=MarketResponse)
async def get_market(
    market_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupère un marché par son ID
    
    Args:
        market_id: ID du marché
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Marché demandé
        
    Raises:
        HTTPException: Si le marché n'existe pas
    """
    market = db.query(Market).filter(Market.id == market_id).first()
    
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )
    
    return market


@router.post("/", response_model=MarketResponse, status_code=status.HTTP_201_CREATED)
async def create_market(
    market_data: MarketCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Crée un nouveau marché
    
    Args:
        market_data: Données du marché
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Marché créé
        
    Raises:
        HTTPException: Si l'utilisateur n'a pas les permissions
    """
    if not can_create_market(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create markets"
        )
    
    # Vérifier si le numéro de marché existe déjà
    existing_market = db.query(Market).filter(
        Market.market_number == market_data.market_number
    ).first()
    
    if existing_market:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Market number already exists"
        )
    
    # Créer le marché
    db_market = Market(
        **market_data.model_dump(exclude={'companies'}),
        created_by=current_user.id,
        modified_by=current_user.id,
        participating_companies_count=len(market_data.companies) if market_data.companies else 0
    )
    
    db.add(db_market)
    db.flush()
    
    # Ajouter les entreprises si fournies
    if market_data.companies:
        from app.models.market import Company
        for company_data in market_data.companies:
            db_company = Company(
                **company_data.model_dump(),
                market_id=db_market.id
            )
            db.add(db_company)
    
    db.commit()
    db.refresh(db_market)
    
    return db_market


@router.put("/{market_id}", response_model=MarketResponse)
async def update_market(
    market_id: int,
    market_update: MarketUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Met à jour un marché
    
    Args:
        market_id: ID du marché
        market_update: Données de mise à jour
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Marché mis à jour
        
    Raises:
        HTTPException: Si le marché n'existe pas ou permissions insuffisantes
    """
    if not can_edit_market(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to edit markets"
        )
    
    market = db.query(Market).filter(Market.id == market_id).first()
    
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )
    
    # Mise à jour des champs
    update_data = market_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(market, field, value)
    
    market.modified_by = current_user.id
    db.commit()
    db.refresh(market)
    
    return market


@router.delete("/{market_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_market(
    market_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Supprime un marché
    
    Args:
        market_id: ID du marché
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Raises:
        HTTPException: Si le marché n'existe pas ou permissions insuffisantes
    """
    if not can_delete_market(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete markets"
        )
    
    market = db.query(Market).filter(Market.id == market_id).first()
    
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )
    
    db.delete(market)
    db.commit()
    
    return None


@router.post("/{market_id}/companies", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def add_company(
    market_id: int,
    company_data: CompanyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Ajoute une entreprise à un marché
    
    Args:
        market_id: ID du marché
        company_data: Données de l'entreprise
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Entreprise créée
        
    Raises:
        HTTPException: Si le marché n'existe pas
    """
    market = db.query(Market).filter(Market.id == market_id).first()
    
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )
    
    from app.models.market import Company
    db_company = Company(
        **company_data.model_dump(),
        market_id=market_id
    )
    
    db.add(db_company)
    
    # Mettre à jour le compteur d'entreprises
    market.participating_companies_count += 1
    market.modified_by = current_user.id
    
    db.commit()
    db.refresh(db_company)
    
    return db_company
