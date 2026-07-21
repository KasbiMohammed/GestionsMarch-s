"""
Service de notifications
Gestion des alertes et notifications pour les échéances et retards
"""

from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session
from app.models.stage import Stage, StageStatus
from app.models.market import Market, MarketStatus
from app.utils.date_utils import calculate_delay, get_alert_level


class NotificationService:
    """Service pour la gestion des notifications"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_upcoming_deadlines(self, days_ahead: int = 7) -> List[Dict]:
        """
        Récupère les échéances à venir dans les prochains jours
        
        Args:
            days_ahead: Nombre de jours à l'avance pour l'alerte
            
        Returns:
            Liste des échéances à venir
        """
        upcoming_deadlines = []
        today = datetime.now().date()
        future_date = today + timedelta(days=days_ahead)
        
        # Échéances des étapes
        stages = self.db.query(Stage).filter(
            Stage.planned_date.between(today, future_date),
            Stage.status.in_([StageStatus.NOT_STARTED, StageStatus.WAITING])
        ).all()
        
        for stage in stages:
            days_until = (stage.planned_date.date() - today).days if stage.planned_date else 0
            urgency = "high" if days_until <= 2 else ("medium" if days_until <= 5 else "low")
            
            upcoming_deadlines.append({
                'type': 'stage_deadline',
                'entity_id': stage.id,
                'entity_type': 'stage',
                'title': f"Échéance: {stage.name}",
                'description': f"L'étape '{stage.name}' doit être terminée le {stage.planned_date.strftime('%d/%m/%Y')}",
                'due_date': stage.planned_date,
                'days_until': days_until,
                'urgency': urgency,
                'market_id': stage.market_id
            })
        
        # Échéances des marchés
        markets = self.db.query(Market).filter(
            Market.expected_end_date.between(today, future_date),
            Market.status == MarketStatus.EN_COURS
        ).all()
        
        for market in markets:
            days_until = (market.expected_end_date.date() - today).days if market.expected_end_date else 0
            urgency = "high" if days_until <= 2 else ("medium" if days_until <= 5 else "low")
            
            upcoming_deadlines.append({
                'type': 'market_deadline',
                'entity_id': market.id,
                'entity_type': 'market',
                'title': f"Échéance: {market.market_number}",
                'description': f"Le marché '{market.market_number}' doit être terminé le {market.expected_end_date.strftime('%d/%m/%Y')}",
                'due_date': market.expected_end_date,
                'days_until': days_until,
                'urgency': urgency,
                'market_id': market.id
            })
        
        # Trier par urgence et date
        upcoming_deadlines.sort(key=lambda x: (x['urgency'], x['days_until']))
        
        return upcoming_deadlines
    
    def get_overdue_items(self) -> List[Dict]:
        """
        Récupère les éléments en retard
        
        Returns:
            Liste des éléments en retard
        """
        overdue_items = []
        today = datetime.now().date()
        
        # Étapes en retard
        late_stages = self.db.query(Stage).filter(
            Stage.planned_date < today,
            Stage.status.in_([StageStatus.NOT_STARTED, StageStatus.IN_PROGRESS, StageStatus.WAITING]),
            Stage.is_late == True
        ).all()
        
        for stage in late_stages:
            delay_days = calculate_delay(stage.planned_date, datetime.now()) if stage.planned_date else 0
            alert_level = get_alert_level(delay_days)
            
            overdue_items.append({
                'type': 'stage_late',
                'entity_id': stage.id,
                'entity_type': 'stage',
                'title': f"Retard: {stage.name}",
                'description': f"L'étape '{stage.name}' est en retard de {abs(delay_days)} jours",
                'planned_date': stage.planned_date,
                'delay_days': abs(delay_days),
                'alert_level': alert_level,
                'market_id': stage.market_id
            })
        
        # Marchés en retard
        late_markets = self.db.query(Market).filter(
            Market.expected_end_date < today,
            Market.status == MarketStatus.EN_COURS
        ).all()
        
        for market in late_markets:
            delay_days = calculate_delay(market.expected_end_date, datetime.now()) if market.expected_end_date else 0
            
            overdue_items.append({
                'type': 'market_late',
                'entity_id': market.id,
                'entity_type': 'market',
                'title': f"Retard: {market.market_number}",
                'description': f"Le marché '{market.market_number}' est en retard de {abs(delay_days)} jours",
                'planned_date': market.expected_end_date,
                'delay_days': abs(delay_days),
                'alert_level': 'red',
                'market_id': market.id
            })
        
        # Trier par gravité du retard
        overdue_items.sort(key=lambda x: x['delay_days'], reverse=True)
        
        return overdue_items
    
    def get_critical_alerts(self) -> List[Dict]:
        """
        Récupère les alertes critiques (retards importants, échéances urgentes)
        
        Returns:
            Liste des alertes critiques
        """
        critical_alerts = []
        today = datetime.now().date()
        
        # Retards de plus de 7 jours
        very_late_stages = self.db.query(Stage).filter(
            Stage.planned_date < today - timedelta(days=7),
            Stage.status.in_([StageStatus.NOT_STARTED, StageStatus.IN_PROGRESS]),
            Stage.is_late == True
        ).all()
        
        for stage in very_late_stages:
            delay_days = calculate_delay(stage.planned_date, datetime.now()) if stage.planned_date else 0
            
            critical_alerts.append({
                'type': 'critical_stage',
                'entity_id': stage.id,
                'entity_type': 'stage',
                'title': f"CRITIQUE: {stage.name}",
                'description': f"Retard critique de {abs(delay_days)} jours pour l'étape '{stage.name}'",
                'delay_days': abs(delay_days),
                'market_id': stage.market_id
            })
        
        # Échéances dans les 2 jours
        urgent_stages = self.db.query(Stage).filter(
            Stage.planned_date.between(today, today + timedelta(days=2)),
            Stage.status == StageStatus.NOT_STARTED
        ).all()
        
        for stage in urgent_stages:
            critical_alerts.append({
                'type': 'urgent_deadline',
                'entity_id': stage.id,
                'entity_type': 'stage',
                'title': f"URGENT: {stage.name}",
                'description': f"Échéance urgente dans {(stage.planned_date.date() - today).days} jours pour '{stage.name}'",
                'due_date': stage.planned_date,
                'market_id': stage.market_id
            })
        
        return critical_alerts
    
    def get_notification_summary(self) -> Dict:
        """
        Génère un résumé des notifications
        
        Returns:
            Dictionnaire avec le résumé des notifications
        """
        upcoming = self.get_upcoming_deadlines(days_ahead=7)
        overdue = self.get_overdue_items()
        critical = self.get_critical_alerts()
        
        return {
            'upcoming_count': len(upcoming),
            'overdue_count': len(overdue),
            'critical_count': len(critical),
            'upcoming': upcoming[:5],  # Top 5
            'overdue': overdue[:5],     # Top 5
            'critical': critical[:3]    # Top 3
        }
    
    def check_stage_delays(self) -> int:
        """
        Met à jour le statut de retard des étapes
        À exécuter périodiquement (tâche planifiée)
        
        Returns:
            Nombre d'étapes mises à jour
        """
        today = datetime.now()
        updated_count = 0
        
        stages = self.db.query(Stage).filter(
            Stage.planned_date.isnot(None),
            Stage.status.in_([StageStatus.NOT_STARTED, StageStatus.IN_PROGRESS, StageStatus.WAITING])
        ).all()
        
        for stage in stages:
            if stage.planned_date < today:
                stage.calculate_delay()
                updated_count += 1
        
        self.db.commit()
        return updated_count
    
    def check_market_delays(self) -> int:
        """
        Met à jour le statut des marchés en retard
        À exécuter périodiquement (tâche planifiée)
        
        Returns:
            Nombre de marchés mis à jour
        """
        today = datetime.now()
        updated_count = 0
        
        markets = self.db.query(Market).filter(
            Market.expected_end_date.isnot(None),
            Market.status == MarketStatus.EN_COURS
        ).all()
        
        for market in markets:
            if market.expected_end_date < today and not market.actual_end_date:
                market.status = MarketStatus.EN_RETARD
                updated_count += 1
        
        self.db.commit()
        return updated_count


def get_notification_service(db: Session) -> NotificationService:
    """
    Factory pour créer une instance du service de notifications
    
    Args:
        db: Session de base de données
        
    Returns:
        Instance de NotificationService
    """
    return NotificationService(db)
