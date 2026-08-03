"""
API de gestion des marchés publics
Endpoints pour la gestion CRUD des marchés
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.user import User
from app.models.market import Market, MarketStatus
from app.schemas.market import MarketCreate, MarketUpdate, MarketResponse, MarketListResponse, CompanyCreate, CompanyResponse
from app.auth.dependencies import get_current_active_user
from app.auth.permissions import can_create_market, can_edit_market, can_delete_market

router = APIRouter()


# ═══════════════════════════════════════════════════════════════
# SCHÉMA pour la création depuis une planification avec dates
# ═══════════════════════════════════════════════════════════════

class MarketFromPlanningCreate(BaseModel):
    """Données optionnelles à saisir lors de la création depuis une planification"""
    launch_date: Optional[datetime] = Field(None, description="Date de lancement du marché")
    publication_date: Optional[datetime] = Field(None, description="Date de publication / lancement")
    opening_date: Optional[datetime] = Field(None, description="Date d'ouverture des plis")
    attribution_date: Optional[datetime] = Field(None, description="Date d'attribution")
    notification_date: Optional[datetime] = Field(None, description="Date de notification")
    start_date: Optional[datetime] = Field(None, description="Date de démarrage des travaux")
    expected_end_date: Optional[datetime] = Field(None, description="Date prévisionnelle de fin")
    master_of_work: Optional[str] = Field("Commune", description="Maître d'ouvrage")
    observations: Optional[str] = Field(None, description="Observations complémentaires")


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS EXISTANTS (conservés tels quels)
# ═══════════════════════════════════════════════════════════════

@router.get("/available-plannings", response_model=List[dict])
async def get_available_plannings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les planifications disponibles pour créer un marché
    (planifications sans marché associé)
    """
    from app.models.market_planning import MarketPlanning
    
    planning_ids_with_market = db.query(Market.planning_id).filter(
        Market.planning_id.isnot(None)
    ).all()
    planning_ids_with_market = [p[0] for p in planning_ids_with_market]
    
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
    """
    query = db.query(Market)
    
    if status:
        query = query.filter(Market.status == status)
    
    if search:
        query = query.filter(
            (Market.market_number.ilike(f"%{search}%")) |
            (Market.object.ilike(f"%{search}%"))
        )
    
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
    """Récupère un marché par son ID"""
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
    """Crée un nouveau marché"""
    if not can_create_market(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create markets"
        )
    
    existing_market = db.query(Market).filter(
        Market.market_number == market_data.market_number
    ).first()
    
    if existing_market:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Market number already exists"
        )
    
    db_market = Market(
        **market_data.model_dump(exclude={'companies'}),
        created_by=current_user.id,
        modified_by=current_user.id,
        participating_companies_count=len(market_data.companies) if market_data.companies else 0
    )
    
    db.add(db_market)
    db.flush()
    
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
    """Met à jour un marché"""
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
    """Supprime un marché"""
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
    """Ajoute une entreprise à un marché"""
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
    market.participating_companies_count += 1
    market.modified_by = current_user.id
    
    db.commit()
    db.refresh(db_company)
    
    return db_company


# ═══════════════════════════════════════════════════════════════
# CORRECTION CRITIQUE : Création depuis une planification
# ═══════════════════════════════════════════════════════════════

@router.post("/from-planning/{planning_id}", response_model=MarketResponse, status_code=status.HTTP_201_CREATED)
async def create_market_from_planning(
    planning_id: int,
    data: Optional[MarketFromPlanningCreate] = Body(None),  # ← NOUVEAU : dates saisissables
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Crée un marché à partir d'une planification
    
    Permet de saisir les dates de lancement qui sont différentes
    des dates de planification.
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
    
    # ── Mapping des procédures ──
    procedure_mapping = {
        "bon_commande": "bon_commande",
        "marche_simplifie": "marche_simplifie",
        "ao_ouvert": "appel_d_offres_ouvert",
        "ao_restreint": "appel_d_offres_restreint",
        "consultation": "consultation",
        "procedure_negociee": "procedure_negociee",
        "appel_d_offres_ouvert": "appel_d_offres_ouvert",
        "appel_d_offres_restreint": "appel_d_offres_restreint",
        "procedure_adaptee": "procedure_adaptee",
        "marche_direct": "marche_direct"
    }
    
    # ── Mapping des types de projet ──
    project_mapping = {
        "travaux": "travaux",
        "fournitures": "fournitures",
        "services": "services",
        "prestations_intellectuelles": "prestations_intellectuelles"
    }
    
    # Récupérer les valeurs mappées (ou valeurs brutes si pas de mapping)
    raw_procedure = planning.procedure_type.value if planning.procedure_type else None
    raw_project = planning.project_type.value if planning.project_type else None
    
    procurement_method = procedure_mapping.get(raw_procedure, raw_procedure or "appel_d_offres_ouvert")
    market_type = project_mapping.get(raw_project, raw_project or "services")
    
    # Générer un numéro de marché lisible
    import uuid
    market_number = f"M-{planning.fiscal_year}-{uuid.uuid4().hex[:6].upper()}"
    
    # ── Construction de l'objet du marché (jamais vide) ──
    market_object = planning.title if planning.title else ""
    if not market_object and planning.description:
        market_object = planning.description
    if not market_object:
        market_object = f"Marché {market_type} - {planning.fiscal_year}"
    
    # ── Dates : celles saisies par l'utilisateur prioritaires ──
    dates = data or MarketFromPlanningCreate()
    
    market = Market(
        market_number=market_number,
        object=market_object,
        master_of_work=dates.master_of_work or "Commune",
        market_type=market_type,
        procurement_method=procurement_method,
        estimated_amount=planning.estimated_budget or 0.0,
        budget=planning.estimated_budget or 0.0,
        responsible_service=planning.requesting_service_name,
        follow_up_responsible=planning.responsible_name,
        
        # Dates de lancement du marché (saisies par l'utilisateur)
        launch_date=dates.launch_date,
        publication_date=dates.publication_date,
        opening_date=dates.opening_date,
        attribution_date=dates.attribution_date,
        notification_date=dates.notification_date,
        start_date=dates.start_date,
        expected_end_date=dates.expected_end_date,
        
        observations=dates.observations or planning.observations,
        planning_id=planning_id,
        created_by=current_user.id,
        modified_by=current_user.id,
        
        # Statut par défaut: en préparation (plus de "planifié")
        status=MarketStatus.EN_PREPARATION,
        progress_percentage=0
    )
    
    db.add(market)
    db.commit()
    db.refresh(market)
    
    # Historique
    from app.models.history import History
    history = History(
        market_id=market.id,
        action="Création",
        description=f"Marché {market_number} créé à partir de la planification {planning.planning_number}",
        user_id=current_user.id
    )
    db.add(history)
    db.commit()
    
    return market