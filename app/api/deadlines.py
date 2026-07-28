"""
API endpoints pour la gestion des délais réglementaires
Module dédié - ne modifie pas les fonctionnalités existantes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime

from app.database import get_db
from app.services.deadline_service import DeadlineService
from app.models.deadline import (
    Deadline, DeadlineSettings, DeadlineAlert, DeadlineNotification,
    DeadlineType, AlertLevel, DeadlineStatus, NotificationStatus
)
from app.models.user import User
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/deadlines", tags=["deadlines"])


# ============================================
# ENDPOINTS POUR LES DÉLAIS
# ============================================

@router.post("/", response_model=dict)
def create_deadline(
    deadline_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée un nouveau délai réglementaire
    """
    deadline_service = DeadlineService(db)
    deadline_data['created_by'] = current_user.id
    deadline = deadline_service.create_deadline(deadline_data)
    
    return {
        "id": deadline.id,
        "message": "Délai créé avec succès"
    }


@router.get("/{deadline_id}", response_model=dict)
def get_deadline(
    deadline_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupère un délai par son ID
    """
    deadline_service = DeadlineService(db)
    deadline = deadline_service.get_deadline(deadline_id)
    if not deadline:
        raise HTTPException(status_code=404, detail="Délai non trouvé")
    
    return {
        "id": deadline.id,
        "deadline_type": deadline.deadline_type.value,
        "market_id": deadline.market_id,
        "planning_id": deadline.planning_id,
        "offer_id": deadline.offer_id,
        "start_date": deadline.start_date.isoformat() if deadline.start_date else None,
        "due_date": deadline.due_date.isoformat() if deadline.due_date else None,
        "completed_date": deadline.completed_date.isoformat() if deadline.completed_date else None,
        "days_remaining": deadline.days_remaining,
        "days_overdue": deadline.days_overdue,
        "alert_level": deadline.alert_level.value,
        "status": deadline.status.value,
        "title": deadline.title,
        "description": deadline.description,
        "reference": deadline.reference,
        "original_due_date": deadline.original_due_date.isoformat() if deadline.original_due_date else None,
        "extension_count": deadline.extension_count,
        "extension_reason": deadline.extension_reason,
        "created_at": deadline.created_at.isoformat() if deadline.created_at else None,
        "updated_at": deadline.updated_at.isoformat() if deadline.updated_at else None
    }


@router.put("/{deadline_id}", response_model=dict)
def update_deadline(
    deadline_id: int,
    deadline_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Met à jour un délai
    """
    deadline_service = DeadlineService(db)
    deadline_data['updated_by'] = current_user.id
    deadline = deadline_service.update_deadline(deadline_id, deadline_data)
    
    return {
        "id": deadline.id,
        "message": "Délai mis à jour avec succès"
    }


@router.delete("/{deadline_id}", response_model=dict)
def delete_deadline(
    deadline_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprime un délai
    """
    deadline_service = DeadlineService(db)
    success = deadline_service.delete_deadline(deadline_id)
    if not success:
        raise HTTPException(status_code=404, detail="Délai non trouvé")
    
    return {"message": "Délai supprimé avec succès"}


@router.get("/market/{market_id}", response_model=List[dict])
def get_deadlines_by_market(
    market_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupère tous les délais d'un marché
    """
    deadline_service = DeadlineService(db)
    deadlines = deadline_service.get_deadlines_by_market(market_id)
    
    return [{
        "id": d.id,
        "deadline_type": d.deadline_type.value,
        "title": d.title,
        "due_date": d.due_date.isoformat() if d.due_date else None,
        "days_remaining": d.days_remaining,
        "days_overdue": d.days_overdue,
        "alert_level": d.alert_level.value,
        "status": d.status.value
    } for d in deadlines]


@router.get("/type/{deadline_type}", response_model=List[dict])
def get_deadlines_by_type(
    deadline_type: str,
    db: Session = Depends(get_db)
):
    """
    Récupère tous les délais d'un type donné
    """
    deadline_service = DeadlineService(db)
    try:
        deadline_type_enum = DeadlineType(deadline_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Type de délai invalide")
    
    deadlines = deadline_service.get_deadlines_by_type(deadline_type_enum)
    
    return [{
        "id": d.id,
        "deadline_type": d.deadline_type.value,
        "title": d.title,
        "due_date": d.due_date.isoformat() if d.due_date else None,
        "days_remaining": d.days_remaining,
        "days_overdue": d.days_overdue,
        "alert_level": d.alert_level.value,
        "status": d.status.value
    } for d in deadlines]


@router.post("/{deadline_id}/recalculate", response_model=dict)
def recalculate_deadline(
    deadline_id: int,
    db: Session = Depends(get_db)
):
    """
    Recalcule le statut d'un délai
    """
    deadline_service = DeadlineService(db)
    deadline = deadline_service.update_deadline_calculations(deadline_id)
    
    return {
        "id": deadline.id,
        "days_remaining": deadline.days_remaining,
        "days_overdue": deadline.days_overdue,
        "alert_level": deadline.alert_level.value,
        "status": deadline.status.value,
        "message": "Calcul mis à jour avec succès"
    }


# ============================================
# ENDPOINTS POUR LES PARAMÈTRES
# ============================================

@router.get("/settings/", response_model=List[dict])
def get_settings(
    deadline_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Récupère les paramètres de délais
    """
    deadline_service = DeadlineService(db)
    deadline_type_enum = None
    if deadline_type:
        try:
            deadline_type_enum = DeadlineType(deadline_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Type de délai invalide")
    
    settings_list = deadline_service.get_settings(deadline_type_enum)
    
    return [{
        "id": s.id,
        "deadline_type": s.deadline_type.value,
        "type_name": s.type_name,
        "description": s.description,
        "j1": s.j1,
        "j2": s.j2,
        "j3": s.j3,
        "critique": s.critique,
        "activation": s.activation,
        "default_days": s.default_days,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None
    } for s in settings_list]


@router.put("/settings/{settings_id}", response_model=dict)
def update_settings(
    settings_id: int,
    settings_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Met à jour les paramètres d'un type de délai
    """
    deadline_service = DeadlineService(db)
    settings_data['updated_by'] = current_user.id
    settings = deadline_service.update_settings(settings_id, settings_data)
    
    return {
        "id": settings.id,
        "message": "Paramètres mis à jour avec succès"
    }


# ============================================
# ENDPOINTS POUR LES STATISTIQUES
# ============================================

@router.get("/statistics/summary", response_model=dict)
def get_statistics(
    db: Session = Depends(get_db)
):
    """
    Récupère les statistiques globales des délais
    """
    deadline_service = DeadlineService(db)
    stats = deadline_service.get_deadline_statistics()
    return stats


@router.get("/statistics/upcoming", response_model=List[dict])
def get_upcoming_deadlines(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Récupère les délais à venir dans les X jours
    """
    deadline_service = DeadlineService(db)
    deadlines = deadline_service.get_upcoming_deadlines(days)
    
    return [{
        "id": d.id,
        "deadline_type": d.deadline_type.value,
        "title": d.title,
        "due_date": d.due_date.isoformat() if d.due_date else None,
        "days_remaining": d.days_remaining,
        "alert_level": d.alert_level.value,
        "market_id": d.market_id
    } for d in deadlines]


@router.get("/statistics/overdue", response_model=List[dict])
def get_overdue_deadlines(
    db: Session = Depends(get_db)
):
    """
    Récupère tous les délais dépassés
    """
    deadline_service = DeadlineService(db)
    deadlines = deadline_service.get_overdue_deadlines()
    
    return [{
        "id": d.id,
        "deadline_type": d.deadline_type.value,
        "title": d.title,
        "due_date": d.due_date.isoformat() if d.due_date else None,
        "days_overdue": d.days_overdue,
        "alert_level": d.alert_level.value,
        "market_id": d.market_id
    } for d in deadlines]


@router.get("/statistics/critical", response_model=List[dict])
def get_critical_deadlines(
    db: Session = Depends(get_db)
):
    """
    Récupère tous les délais critiques
    """
    deadline_service = DeadlineService(db)
    deadlines = deadline_service.get_critical_deadlines()
    
    return [{
        "id": d.id,
        "deadline_type": d.deadline_type.value,
        "title": d.title,
        "due_date": d.due_date.isoformat() if d.due_date else None,
        "days_remaining": d.days_remaining,
        "alert_level": d.alert_level.value,
        "market_id": d.market_id
    } for d in deadlines]


@router.get("/calendar/events", response_model=List[dict])
def get_calendar_events(
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db)
):
    """
    Récupère les délais pour une période donnée (pour le calendrier)
    """
    deadline_service = DeadlineService(db)
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Format de date invalide (ISO format attendu)")
    
    events = deadline_service.get_deadlines_for_calendar(start, end)
    return events


# ============================================
# ENDPOINTS POUR LES ALERTES
# ============================================

@router.get("/alerts/", response_model=List[dict])
def get_alerts(
    acknowledged: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Récupère les alertes
    """
    deadline_service = DeadlineService(db)
    alerts = deadline_service.get_alerts(acknowledged)
    
    return [{
        "id": a.id,
        "deadline_id": a.deadline_id,
        "alert_level": a.alert_level.value,
        "alert_date": a.alert_date.isoformat() if a.alert_date else None,
        "acknowledged": a.acknowledged,
        "acknowledged_by": a.acknowledged_by,
        "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
        "message": a.message,
        "created_at": a.created_at.isoformat() if a.created_at else None
    } for a in alerts]


@router.post("/alerts/{alert_id}/acknowledge", response_model=dict)
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reconnaît une alerte
    """
    deadline_service = DeadlineService(db)
    success = deadline_service.acknowledge_alert(alert_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Alerte non trouvée")
    
    return {"message": "Alerte reconnue avec succès"}


# ============================================
# ENDPOINTS POUR LES NOTIFICATIONS
# ============================================

@router.get("/notifications/", response_model=List[dict])
def get_notifications(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les notifications de l'utilisateur connecté
    """
    deadline_service = DeadlineService(db)
    status_enum = None
    if status:
        try:
            status_enum = NotificationStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Statut de notification invalide")
    
    notifications = deadline_service.get_notifications(current_user.id, status_enum)
    
    return [{
        "id": n.id,
        "deadline_id": n.deadline_id,
        "title": n.title,
        "message": n.message,
        "status": n.status.value,
        "scheduled_date": n.scheduled_date.isoformat() if n.scheduled_date else None,
        "sent_date": n.sent_date.isoformat() if n.sent_date else None,
        "read_date": n.read_date.isoformat() if n.read_date else None,
        "notification_type": n.notification_type,
        "created_at": n.created_at.isoformat() if n.created_at else None
    } for n in notifications]


@router.post("/notifications/{notification_id}/read", response_model=dict)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """
    Marque une notification comme lue
    """
    deadline_service = DeadlineService(db)
    success = deadline_service.mark_notification_read(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification non trouvée")
    
    return {"message": "Notification marquée comme lue"}
