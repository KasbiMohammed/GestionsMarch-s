"""
API du Dashboard de Supervision
Module de pilotage global avec KPI en temps réel
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.auth.permissions import can_view_planning
from app.database import get_db
from app.models.user import User
from app.services.supervision_service import SupervisionService

router = APIRouter()


def get_supervision_service(db: Session) -> SupervisionService:
    """Dependency injection pour le service de supervision."""
    return SupervisionService(db)


@router.get("/kpis")
async def get_global_kpis(
    year: Optional[int] = Query(None),
    service_id: Optional[int] = Query(None),
    procedure_type: Optional[str] = Query(None),
    project_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Récupère tous les KPI globaux du dashboard avec filtres."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_supervision_service(db)
    
    filters = {}
    if year:
        filters['year'] = year
    if service_id:
        filters['service_id'] = service_id
    if procedure_type:
        filters['procedure_type'] = procedure_type
    if project_type:
        filters['project_type'] = project_type
    if status:
        filters['status'] = status
    
    return service.get_global_kpis(filters)


@router.get("/kpis/summary")
async def get_kpis_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Résumé des KPI principaux pour le dashboard."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_supervision_service(db)
    kpis = service.get_global_kpis()
    
    return {
        "total_markets": kpis["total_markets"],
        "active_markets": kpis["markets_by_state"]["actifs"],
        "terminated_markets": kpis["markets_by_state"]["termines"],
        "global_progress": kpis["global_progress_rate"],
        "delayed_markets": kpis["delayed_markets"],
        "upcoming_deadlines": kpis["upcoming_deadlines"],
        "validations_pending": kpis["validations_pending"],
        "critical_alerts": kpis["critical_alerts"],
        "budget_programme": kpis["budget_indicators"]["programme"],
        "budget_engage": kpis["budget_indicators"]["engage"],
    }


@router.get("/markets/by-status")
async def get_markets_by_status(
    year: Optional[int] = Query(None),
    service_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Répartition des marchés par statut."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_supervision_service(db)
    filters = {}
    if year:
        filters['year'] = year
    if service_id:
        filters['service_id'] = service_id
    
    return service.get_markets_by_status(filters)


@router.get("/markets/by-type")
async def get_markets_by_type(
    year: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Répartition des marchés par type."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_supervision_service(db)
    filters = {}
    if year:
        filters['year'] = year
    
    return service.get_by_market_type(filters)


@router.get("/markets/by-procedure")
async def get_markets_by_procedure(
    year: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Répartition des marchés par procédure."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_supervision_service(db)
    filters = {}
    if year:
        filters['year'] = year
    
    return service.get_by_procedure(filters)


@router.get("/markets/by-service")
async def get_markets_by_service(
    year: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Répartition des marchés par service."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_supervision_service(db)
    filters = {}
    if year:
        filters['year'] = year
    
    return service.get_by_service(filters)


@router.get("/budget/indicators")
async def get_budget_indicators(
    year: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Indicateurs budgétaires."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_supervision_service(db)
    filters = {}
    if year:
        filters['year'] = year
    
    return service.get_budget_indicators(filters)


@router.get("/top/risk")
async def get_top_risk_markets(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Top N marchés à risque."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_supervision_service(db)
    return service.get_top_risk_markets({})[:limit]


@router.get("/top/delayed")
async def get_top_delayed_markets(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Top N marchés en retard."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_supervision_service(db)
    return service.get_top_delayed_markets({})[:limit]


@router.get("/top/upcoming")
async def get_top_upcoming_deadlines(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Top N marchés proches de leur échéance."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_supervision_service(db)
    return service.get_top_upcoming_deadlines({})[:limit]


@router.get("/calendar")
async def get_upcoming_calendar(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Calendrier des prochaines échéances."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_supervision_service(db)
    return service.get_upcoming_calendar({})


@router.get("/activities")
async def get_recent_activities(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Activités récentes."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_supervision_service(db)
    return service.get_recent_activities({})[:limit]
