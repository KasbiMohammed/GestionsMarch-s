"""
API du tableau de bord
Endpoints pour les statistiques, KPIs et graphiques
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Dict, Any
from datetime import datetime, timedelta

from app.database import get_db
from app.models.user import User
from app.models.market import Market, MarketStatus
from app.models.stage import Stage, StageStatus
from app.auth.dependencies import get_current_active_user

router = APIRouter()


@router.get("/statistics")
async def get_dashboard_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Récupère les statistiques globales du tableau de bord
    
    Args:
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Statistiques du tableau de bord
    """
    # Statistiques des marchés
    total_markets = db.query(Market).count()
    markets_en_cours = db.query(Market).filter(Market.status == MarketStatus.EN_COURS).count()
    markets_termine = db.query(Market).filter(Market.status == MarketStatus.TERMINE).count()
    markets_en_retard = db.query(Market).filter(Market.status == MarketStatus.EN_RETARD).count()
    markets_en_attente = db.query(Market).filter(Market.status == MarketStatus.EN_ATTENTE).count()
    
    # Montants
    total_estimated = db.query(func.sum(Market.estimated_amount)).scalar() or 0
    total_definitive = db.query(func.sum(Market.definitive_amount)).scalar() or 0
    
    # Progression moyenne
    avg_progress = db.query(func.avg(Market.progress_percentage)).scalar() or 0
    
    # Statistiques des étapes
    total_stages = db.query(Stage).count()
    stages_completed = db.query(Stage).filter(Stage.status == StageStatus.COMPLETED).count()
    stages_in_progress = db.query(Stage).filter(Stage.status == StageStatus.IN_PROGRESS).count()
    stages_late = db.query(Stage).filter(Stage.is_late == True).count()
    
    return {
        "markets": {
            "total": total_markets,
            "en_cours": markets_en_cours,
            "termine": markets_termine,
            "en_retard": markets_en_retard,
            "en_attente": markets_en_attente,
            "planifie": total_markets - markets_en_cours - markets_termine - markets_en_retard - markets_en_attente
        },
        "amounts": {
            "total_estimated": float(total_estimated),
            "total_definitive": float(total_definitive)
        },
        "progress": {
            "average": float(avg_progress)
        },
        "stages": {
            "total": total_stages,
            "completed": stages_completed,
            "in_progress": stages_in_progress,
            "late": stages_late
        }
    }


@router.get("/markets-by-status")
async def get_markets_by_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, int]:
    """
    Récupère le nombre de marchés par statut
    
    Args:
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Dictionnaire des comptes par statut
    """
    status_counts = {}
    
    for status in MarketStatus:
        count = db.query(Market).filter(Market.status == status).count()
        status_counts[status.value] = count
    
    return status_counts


@router.get("/markets-by-type")
async def get_markets_by_type(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, int]:
    """
    Récupère le nombre de marchés par type
    
    Args:
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Dictionnaire des comptes par type
    """
    from app.models.market import MarketType
    
    type_counts = {}
    
    for market_type in MarketType:
        count = db.query(Market).filter(Market.market_type == market_type).count()
        type_counts[market_type.value] = count
    
    return type_counts


@router.get("/recent-markets")
async def get_recent_markets(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les marchés les plus récents
    
    Args:
        limit: Nombre maximum de marchés à retourner
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Liste des marchés récents
    """
    from app.schemas.market import MarketResponse
    
    markets = db.query(Market).order_by(Market.created_at.desc()).limit(limit).all()
    return [MarketResponse.model_validate(market) for market in markets]


@router.get("/late-stages")
async def get_late_stages(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les étapes en retard
    
    Args:
        limit: Nombre maximum d'étapes à retourner
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Liste des étapes en retard
    """
    from app.schemas.stage import StageResponse
    
    stages = db.query(Stage).filter(
        Stage.is_late == True
    ).order_by(Stage.delay_days.desc()).limit(limit).all()
    
    return [StageResponse.model_validate(stage) for stage in stages]


@router.get("/monthly-statistics")
async def get_monthly_statistics(
    months: int = 12,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Récupère les statistiques mensuelles sur les derniers mois
    
    Args:
        months: Nombre de mois à analyser
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Statistiques mensuelles
    """
    monthly_data = []
    
    for i in range(months):
        date = datetime.now() - timedelta(days=30 * i)
        month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        
        markets_created = db.query(Market).filter(
            and_(
                Market.created_at >= month_start,
                Market.created_at <= month_end
            )
        ).count()
        
        markets_completed = db.query(Market).filter(
            and_(
                Market.definitive_acceptance_date >= month_start,
                Market.definitive_acceptance_date <= month_end
            )
        ).count()
        
        monthly_data.append({
            "month": month_start.strftime("%Y-%m"),
            "markets_created": markets_created,
            "markets_completed": markets_completed
        })
    
    return {"monthly_data": monthly_data[::-1]}


@router.get("/top-companies")
async def get_top_companies(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les entreprises les plus attributaires
    
    Args:
        limit: Nombre maximum d'entreprises à retourner
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Liste des entreprises les plus attributaires
    """
    from app.models.market import Company
    from sqlalchemy import desc
    
    companies = db.query(
        Company.name,
        func.count(Company.id).label('count'),
        func.sum(Company.offer_amount).label('total_amount')
    ).filter(
        Company.is_attributed == True
    ).group_by(
        Company.name
    ).order_by(
        desc('count')
    ).limit(limit).all()
    
    return [
        {
            "name": company.name,
            "markets_count": company.count,
            "total_amount": float(company.total_amount) if company.total_amount else 0
        }
        for company in companies
    ]
