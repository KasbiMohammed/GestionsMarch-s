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


@router.get("/available-plannings", response_model=List[dict])
async def get_available_plannings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les planifications disponibles pour créer un marché
    (planifications sans marché associé)
    
    Args:
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Liste des planifications disponibles
    """
    from app.models.market_planning import MarketPlanning
    
    # Récupérer les IDs des planifications qui ont déjà un marché
    planning_ids_with_market = db.query(Market.planning_id).filter(
        Market.planning_id.isnot(None)
    ).all()
    planning_ids_with_market = [p[0] for p in planning_ids_with_market]
    
    # Récupérer les planifications sans marché
    available_plannings = db.query(MarketPlanning).filter(
        ~MarketPlanning.id.in_(planning_ids_with_market) if planning_ids_with_market else True
    ).order_by(MarketPlanning.created_at.desc()).all()
    
    return [
        {
            "id": p.id,
            "planning_number": p.planning_number,
            "fiscal_year": p.fiscal_year,
            "title": p.title,
            "description": p.description,
            "project_type": p.project_type.value if p.project_type else None,
            "procedure_type": p.procedure_type.value if p.procedure_type else None,
            "estimated_budget": p.estimated_budget,
            "funding_source": p.funding_source,
            "requesting_service_name": p.requesting_service_name,
            "responsible_name": p.responsible_name,
            "priority": p.priority.value if p.priority else None,
            "status": p.status.value if p.status else None,
            "launch_date": p.launch_date.isoformat() if p.launch_date else None,
            "bid_opening_date": p.bid_opening_date.isoformat() if p.bid_opening_date else None,
            "attribution_date": p.attribution_date.isoformat() if p.attribution_date else None,
            "notification_date": p.notification_date.isoformat() if p.notification_date else None,
            "service_order_date": p.service_order_date.isoformat() if p.service_order_date else None,
            "start_date": p.start_date.isoformat() if p.start_date else None,
            "end_date": p.end_date.isoformat() if p.end_date else None,
            "observations": p.observations
        }
        for p in available_plannings
    ]


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


@router.post("/from-planning/{planning_id}", response_model=MarketResponse, status_code=status.HTTP_201_CREATED)
async def create_market_from_planning(
    planning_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Crée un marché à partir d'une planification
    
    Args:
        planning_id: ID de la planification
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Marché créé
        
    Raises:
        HTTPException: Si la planification n'existe pas ou a déjà un marché
    """
    from app.models.market_planning import MarketPlanning
    from app.models.market import MarketType, ProcurementMethod
    
    # Vérifier si la planification existe
    planning = db.query(MarketPlanning).filter(MarketPlanning.id == planning_id).first()
    if not planning:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planning not found"
        )
    
    # Vérifier si la planification a déjà un marché
    existing_market = db.query(Market).filter(Market.planning_id == planning_id).first()
    if existing_market:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A market already exists for this planning"
        )
    
    # Mapper les types de procédure de planification vers les types de marché
    procedure_mapping = {
        "bon_commande": ProcurementMethod.BON_COMMANDE,
        "marche_simplifie": ProcurementMethod.MARCHE_SIMPLIFIE,
        "ao_ouvert": ProcurementMethod.APPEL_OFFRES_OUVERT,
        "ao_restreint": ProcurementMethod.APPEL_OFFRES_RESTREINT,
        "consultation": ProcurementMethod.CONSULTATION,
        "procedure_negociee": ProcurementMethod.MARCHE_NEGOCIE
    }
    
    # Mapper les types de projet de planification vers les types de marché
    project_mapping = {
        "travaux": MarketType.TRAVAUX,
        "fournitures": MarketType.FOURNITURES,
        "services": MarketType.SERVICES,
        "prestations_intellectuelles": MarketType.ETUDES
    }
    
    procurement_method = procedure_mapping.get(planning.procedure_type.value) if planning.procedure_type else ProcurementMethod.APPEL_OFFRES_OUVERT
    market_type = project_mapping.get(planning.project_type.value) if planning.project_type else MarketType.SERVICES
    
    # Générer un numéro de marché
    import uuid
    market_number = f"M-{planning.fiscal_year}-{uuid.uuid4().hex[:8].upper()}"
    
    # Créer le marché avec les données de la planification
    from datetime import datetime
    
    market = Market(
        market_number=market_number,
        object=planning.title or planning.description or "",
        master_of_work="Commune",  # Valeur par défaut, peut être personnalisé
        market_type=market_type,
        procurement_method=procurement_method,
        estimated_amount=planning.estimated_budget or 0.0,
        budget=planning.estimated_budget or 0.0,
        responsible_service=planning.requesting_service_name,
        follow_up_responsible=planning.responsible_name,
        # Utiliser les dates de planification seulement si elles sont définies
        publication_date=planning.launch_date if planning.launch_date else None,
        opening_date=planning.bid_opening_date if planning.bid_opening_date else None,
        attribution_date=planning.attribution_date if planning.attribution_date else None,
        notification_date=planning.notification_date if planning.notification_date else None,
        start_date=planning.start_date if planning.start_date else None,
        expected_end_date=planning.end_date if planning.end_date else None,
        observations=planning.observations,
        planning_id=planning_id,
        created_by=current_user.id,
        modified_by=current_user.id,
        status=MarketStatus.PLANIFIE
    )
    
    db.add(market)
    db.commit()
    db.refresh(market)
    
    return market
