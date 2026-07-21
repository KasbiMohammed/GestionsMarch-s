"""
Tâches Celery pour les notifications
Envoi automatique des notifications et alertes
"""

from datetime import datetime, timedelta
from celery import current_task
from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.services.notification_service import NotificationService
from app.services.export_service import ExportService
from app.dashboard.statistics import StatisticsService
from app.dashboard.kpis import KPIService


@celery_app.task(bind=True)
def check_delays(self):
    """
    Vérifie les retards et met à jour les statuts
    Exécuté toutes les heures
    """
    try:
        db = SessionLocal()
        notification_service = NotificationService(db)
        
        # Vérifier les retards des étapes
        stages_updated = notification_service.check_stage_delays()
        
        # Vérifier les retards des marchés
        markets_updated = notification_service.check_market_delays()
        
        db.close()
        
        return {
            'status': 'success',
            'stages_updated': stages_updated,
            'markets_updated': markets_updated,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


@celery_app.task(bind=True)
def send_daily_report(self):
    """
    Envoie un rapport quotidien des notifications
    Exécuté tous les jours
    """
    try:
        db = SessionLocal()
        notification_service = NotificationService(db)
        kpi_service = KPIService(db)
        
        # Récupérer le résumé des notifications
        summary = notification_service.get_notification_summary()
        
        # Récupérer les KPIs d'alertes
        alert_kpis = kpi_service.get_alert_kpis()
        
        db.close()
        
        # Ici, vous pourriez envoyer un email avec le rapport
        # Pour l'instant, on le log
        print(f"Rapport quotidien: {summary}")
        print(f"KPIs d'alertes: {alert_kpis}")
        
        return {
            'status': 'success',
            'summary': summary,
            'alert_kpis': alert_kpis,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


@celery_app.task(bind=True)
def send_deadline_reminder(self, stage_id: int):
    """
    Envoie un rappel pour une échéance d'étape
    """
    try:
        db = SessionLocal()
        from app.models.stage import Stage
        
        stage = db.query(Stage).filter(Stage.id == stage_id).first()
        if stage:
            # Logique d'envoi de notification
            print(f"Rappel pour l'étape {stage.name} du marché {stage.market_id}")
        
        db.close()
        
        return {
            'status': 'success',
            'stage_id': stage_id,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


@celery_app.task(bind=True)
def send_market_deadline_reminder(self, market_id: int):
    """
    Envoie un rappel pour une échéance de marché
    """
    try:
        db = SessionLocal()
        from app.models.market import Market
        
        market = db.query(Market).filter(Market.id == market_id).first()
        if market:
            # Logique d'envoi de notification
            print(f"Rappel pour le marché {market.market_number}")
        
        db.close()
        
        return {
            'status': 'success',
            'market_id': market_id,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
