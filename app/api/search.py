"""
API de recherche avancée
Endpoints pour la recherche multi-critères
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.market import Market, MarketStatus, MarketType, ProcurementMethod
from app.schemas.market import MarketResponse, MarketListResponse
from app.auth.dependencies import get_current_active_user

router = APIRouter()


@router.get("/", response_model=MarketListResponse)
async def search_markets(
    query: Optional[str] = Query(None, description="Recherche textuelle (numéro, objet, entreprise)"),
    market_number: Optional[str] = Query(None, description="Numéro du marché"),
    status: Optional[MarketStatus] = Query(None, description="Statut du marché"),
    market_type: Optional[MarketType] = Query(None, description="Type de marché"),
    procurement_method: Optional[ProcurementMethod] = Query(None, description="Mode de passation"),
    min_amount: Optional[float] = Query(None, ge=0, description="Montant minimum"),
    max_amount: Optional[float] = Query(None, ge=0, description="Montant maximum"),
    start_date_from: Optional[datetime] = Query(None, description="Date de début depuis"),
    start_date_to: Optional[datetime] = Query(None, description="Date de début jusqu'à"),
    end_date_from: Optional[datetime] = Query(None, description="Date de fin depuis"),
    end_date_to: Optional[datetime] = Query(None, description="Date de fin jusqu'à"),
    responsible_service: Optional[str] = Query(None, description="Service responsable"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Recherche avancée de marchés avec filtres multiples
    
    Args:
        query: Recherche textuelle
        market_number: Numéro du marché
        status: Statut du marché
        market_type: Type de marché
        procurement_method: Mode de passation
        min_amount: Montant minimum
        max_amount: Montant maximum
        start_date_from: Date de début depuis
        start_date_to: Date de début jusqu'à
        end_date_from: Date de fin depuis
        end_date_to: Date de fin jusqu'à
        responsible_service: Service responsable
        skip: Nombre de résultats à sauter
        limit: Nombre maximum de résultats
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Liste paginée des marchés correspondants
    """
    from app.models.market import Company
    
    # Construction de la requête
    query_builder = db.query(Market)
    
    # Recherche textuelle
    if query:
        query_builder = query_builder.filter(
            (Market.market_number.ilike(f"%{query}%")) |
            (Market.object.ilike(f"%{query}%")) |
            (Market.master_of_work.ilike(f"%{query}%"))
        )
    
    # Filtres exacts
    if market_number:
        query_builder = query_builder.filter(Market.market_number.ilike(f"%{market_number}%"))
    
    if status:
        query_builder = query_builder.filter(Market.status == status)
    
    if market_type:
        query_builder = query_builder.filter(Market.market_type == market_type)
    
    if procurement_method:
        query_builder = query_builder.filter(Market.procurement_method == procurement_method)
    
    if responsible_service:
        query_builder = query_builder.filter(Market.responsible_service.ilike(f"%{responsible_service}%"))
    
    # Filtres de montant
    if min_amount:
        query_builder = query_builder.filter(Market.estimated_amount >= min_amount)
    
    if max_amount:
        query_builder = query_builder.filter(Market.estimated_amount <= max_amount)
    
    # Filtres de dates
    if start_date_from:
        query_builder = query_builder.filter(Market.start_date >= start_date_from)
    
    if start_date_to:
        query_builder = query_builder.filter(Market.start_date <= start_date_to)
    
    if end_date_from:
        query_builder = query_builder.filter(Market.expected_end_date >= end_date_from)
    
    if end_date_to:
        query_builder = query_builder.filter(Market.expected_end_date <= end_date_to)
    
    # Pagination
    total = query_builder.count()
    markets = query_builder.order_by(Market.created_at.desc()).offset(skip).limit(limit).all()
    
    return MarketListResponse(
        items=markets,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        total_pages=(total + limit - 1) // limit
    )


@router.get("/companies")
async def search_companies(
    query: str = Query(..., description="Nom de l'entreprise"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Recherche d'entreprises
    
    Args:
        query: Nom de l'entreprise
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Liste des entreprises correspondantes
    """
    from app.models.market import Company
    
    companies = db.query(Company).filter(
        Company.name.ilike(f"%{query}%")
    ).all()
    
    return companies


@router.get("/suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=2, description="Terme de recherche"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupère des suggestions de recherche
    
    Args:
        query: Terme de recherche
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Suggestions de recherche
    """
    # Suggestions de numéros de marché
    market_numbers = db.query(Market.market_number).filter(
        Market.market_number.ilike(f"%{query}%")
    ).distinct().limit(5).all()
    
    # Suggestions d'objets de marché
    objects = db.query(Market.object).filter(
        Market.object.ilike(f"%{query}%")
    ).distinct().limit(5).all()
    
    # Suggestions de services
    services = db.query(Market.responsible_service).filter(
        Market.responsible_service.ilike(f"%{query}%")
    ).distinct().limit(5).all()
    
    return {
        "market_numbers": [m[0] for m in market_numbers],
        "objects": [o[0] for o in objects],
        "services": [s[0] for s in services]
    }
