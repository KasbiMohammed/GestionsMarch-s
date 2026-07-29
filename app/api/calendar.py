"""
API endpoints pour le Calendrier Intelligent
Module dédié - ne modifie pas les fonctionnalités existantes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.services.calendar_service import CalendarEventAggregator, BudgetTrackingService
from app.models.calendar import CalendarEvent, BudgetTracking
from app.models.user import User
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/calendar", tags=["Calendar"])


# ============================================
# ENDPOINTS POUR LES ÉVÉNEMENTS
# ============================================

@router.get("/events", response_model=List[dict])
def get_events(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    event_type: Optional[str] = None,
    service: Optional[str] = None,
    responsible: Optional[str] = None,
    procedure: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les événements du calendrier avec filtres
    """
    # Convertir les dates si fournies
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    # Agréger les événements
    aggregator = CalendarEventAggregator(db)
    events = aggregator.aggregate_all_events(start_dt, end_dt)
    
    # Appliquer les filtres
    if event_type:
        events = [e for e in events if e.event_type == event_type]
    if service:
        events = [e for e in events if e.service == service]
    if responsible:
        events = [e for e in events if e.responsible == responsible]
    if procedure:
        events = [e for e in events if e.procedure == procedure]
    if status:
        events = [e for e in events if e.status == status]
    
    # Convertir en dict
    return [{
        'id': e.id,
        'source_module': e.source_module,
        'source_entity_id': e.source_entity_id,
        'source_entity_type': e.source_entity_type,
        'event_type': e.event_type,
        'title': e.title,
        'description': e.description,
        'start_date': e.start_date.isoformat() if e.start_date else None,
        'end_date': e.end_date.isoformat() if e.end_date else None,
        'is_all_day': e.is_all_day,
        'service': e.service,
        'responsible': e.responsible,
        'procedure': e.procedure,
        'status': e.status,
        'priority': e.priority,
        'color': e.color,
        'icon': e.icon,
        'metadata': e.metadata
    } for e in events]


@router.get("/events/{event_id}", response_model=dict)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère un événement spécifique
    """
    event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")
    
    return {
        'id': event.id,
        'source_module': event.source_module,
        'source_entity_id': event.source_entity_id,
        'source_entity_type': event.source_entity_type,
        'event_type': event.event_type,
        'title': event.title,
        'description': event.description,
        'start_date': event.start_date.isoformat() if event.start_date else None,
        'end_date': event.end_date.isoformat() if event.end_date else None,
        'is_all_day': event.is_all_day,
        'service': event.service,
        'responsible': event.responsible,
        'procedure': event.procedure,
        'status': event.status,
        'priority': event.priority,
        'color': event.color,
        'icon': event.icon,
        'metadata': event.metadata
    }


@router.post("/events/sync", response_model=dict)
def sync_events(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Synchronise les événements depuis les modules existants
    """
    # Convertir les dates si fournies
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    # Supprimer les anciens événements
    if start_dt and end_dt:
        db.query(CalendarEvent).filter(
            CalendarEvent.start_date >= start_dt,
            CalendarEvent.end_date <= end_dt
        ).delete()
    else:
        db.query(CalendarEvent).delete()
    
    # Agréger les nouveaux événements
    aggregator = CalendarEventAggregator(db)
    events = aggregator.aggregate_all_events(start_dt, end_dt)
    
    # Sauvegarder les événements
    for event in events:
        db.add(event)
    
    db.commit()
    
    return {
        'message': f'{len(events)} événements synchronisés avec succès',
        'count': len(events)
    }


# ============================================
# ENDPOINTS POUR LE SUIVI BUDGÉTAIRE
# ============================================

@router.get("/budget/annual/{year}", response_model=dict)
def get_annual_budget(
    year: int,
    service: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère le budget annuel
    """
    budget_service = BudgetTrackingService(db)
    budget_data = budget_service.calculate_annual_budget(year, service)
    
    return budget_data


@router.get("/budget/monthly/{year}", response_model=List[dict])
def get_monthly_budget(
    year: int,
    service: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère le budget mensuel pour une année
    """
    budget_service = BudgetTrackingService(db)
    monthly_data = budget_service.calculate_monthly_budget(year, service)
    
    return monthly_data


@router.post("/budget/sync/{year}", response_model=dict)
def sync_budget(
    year: int,
    service: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Synchronise le suivi budgétaire
    """
    budget_service = BudgetTrackingService(db)
    budget_service.sync_budget_tracking(year, service)
    
    return {
        'message': f'Budget {year} synchronisé avec succès',
        'year': year,
        'service': service
    }


# ============================================
# ENDPOINTS POUR LES FILTRES
# ============================================

@router.get("/filters/services", response_model=List[str])
def get_services(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère la liste des services disponibles
    """
    from app.models.market import Market
    
    services = db.query(Market.service).distinct().filter(
        Market.service.isnot(None)
    ).all()
    
    return [s[0] for s in services if s[0]]


@router.get("/filters/responsibles", response_model=List[str])
def get_responsibles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère la liste des responsables disponibles
    """
    from app.models.market import Market
    
    responsibles = db.query(Market.responsible).distinct().filter(
        Market.responsible.isnot(None)
    ).all()
    
    return [r[0] for r in responsibles if r[0]]


@router.get("/filters/procedures", response_model=List[str])
def get_procedures(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère la liste des procédures disponibles
    """
    from app.models.market import Market
    
    procedures = db.query(Market.procedure).distinct().filter(
        Market.procedure.isnot(None)
    ).all()
    
    return [p[0] for p in procedures if p[0]]


@router.get("/filters/statuses", response_model=List[str])
def get_statuses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère la liste des statuts disponibles
    """
    from app.models.market import Market
    
    statuses = db.query(Market.status).distinct().filter(
        Market.status.isnot(None)
    ).all()
    
    return [s[0] for s in statuses if s[0]]


@router.get("/filters/event-types", response_model=List[str])
def get_event_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère la liste des types d'événements
    """
    from app.models.calendar import EventType
    
    return [e.value for e in EventType]
