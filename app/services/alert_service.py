"""
Service des alertes intelligentes
Module 11: Alertes intelligentes
"""

from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.alerts import (
    Alert, AlertRule, AlertType, AlertSeverity, AlertStatus
)
from app.models.execution import Guarantee
from app.models.stage import Stage
from app.models.market import Market


class AlertService:
    """Service pour la gestion des alertes intelligentes"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_guarantee_expiry(self, days_ahead: int = 30) -> List[Alert]:
        """
        Vérifie les garanties arrivant à expiration
        
        Args:
            days_ahead: Nombre de jours à venir
            
        Returns:
            Liste des alertes créées
        """
        cutoff_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        guarantees = self.db.query(Guarantee).filter(
            and_(
                Guarantee.active == True,
                Guarantee.expiry_date <= cutoff_date,
                Guarantee.expiry_date >= datetime.utcnow(),
                Guarantee.expiry_alert_sent == False
            )
        ).all()
        
        alerts = []
        for guarantee in guarantees:
            days_remaining = (guarantee.expiry_date - datetime.utcnow()).days
            severity = AlertSeverity.CRITICAL if days_remaining <= 7 else AlertSeverity.HIGH
            
            alert = Alert(
                alert_type=AlertType.GUARANTEE_EXPIRY,
                severity=severity,
                guarantee_id=guarantee.id,
                market_id=guarantee.market_id,
                title=f"Expiration garantie {guarantee.guarantee_type}",
                message=f"La garantie {guarantee.guarantee_number} expire dans {days_remaining} jours",
                trigger_date=datetime.utcnow(),
                due_date=guarantee.expiry_date,
                created_at=datetime.utcnow()
            )
            
            self.db.add(alert)
            alerts.append(alert)
            
            # Marquer l'alerte comme envoyée
            guarantee.expiry_alert_sent = True
        
        self.db.commit()
        return alerts
    
    def check_stage_delays(self) -> List[Alert]:
        """
        Vérifie les étapes en retard
        
        Returns:
            Liste des alertes créées
        """
        stages = self.db.query(Stage).filter(
            and_(
                Stage.planned_date < datetime.utcnow(),
                Stage.status != 'termine',
                Stage.is_late == False
            )
        ).all()
        
        alerts = []
        for stage in stages:
            delay_days = (datetime.utcnow() - stage.planned_date).days
            
            alert = Alert(
                alert_type=AlertType.STAGE_DELAY,
                severity=AlertSeverity.MEDIUM if delay_days <= 7 else AlertSeverity.HIGH,
                stage_id=stage.id,
                market_id=stage.market_id,
                title=f"Retard étape: {stage.name}",
                message=f"L'étape {stage.name} est en retard de {delay_days} jours",
                trigger_date=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            
            self.db.add(alert)
            alerts.append(alert)
            
            # Marquer l'étape comme en retard
            stage.is_late = True
            stage.delay_days = delay_days
        
        self.db.commit()
        return alerts
    
    def check_market_delays(self) -> List[Alert]:
        """
        Vérifie les marchés en retard
        
        Returns:
            Liste des alertes créées
        """
        markets = self.db.query(Market).filter(
            and_(
                Market.expected_end_date < datetime.utcnow(),
                Market.status != 'termine',
                Market.status != 'annule'
            )
        ).all()
        
        alerts = []
        for market in markets:
            delay_days = (datetime.utcnow() - market.expected_end_date).days
            
            alert = Alert(
                alert_type=AlertType.MARKET_DELAY,
                severity=AlertSeverity.HIGH if delay_days <= 30 else AlertSeverity.CRITICAL,
                market_id=market.id,
                title=f"Retard marché: {market.market_number}",
                message=f"Le marché {market.market_number} est en retard de {delay_days} jours",
                trigger_date=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            
            self.db.add(alert)
            alerts.append(alert)
        
        self.db.commit()
        return alerts
    
    def check_budget_overrun(self) -> List[Alert]:
        """
        Vérifie les dépassements budgétaires
        
        Returns:
            Liste des alertes créées
        """
        markets = self.db.query(Market).filter(
            and_(
                Market.final_amount.isnot(None),
                Market.budget.isnot(None),
                Market.final_amount > Market.budget
            )
        ).all()
        
        alerts = []
        for market in markets:
            overrun_percentage = ((market.final_amount - market.budget) / market.budget) * 100
            
            alert = Alert(
                alert_type=AlertType.BUDGET_OVERRUN,
                severity=AlertSeverity.HIGH if overrun_percentage <= 10 else AlertSeverity.CRITICAL,
                market_id=market.id,
                title=f"Dépassement budgétaire: {market.market_number}",
                message=f"Le marché {market.market_number} a dépassé le budget de {overrun_percentage:.1f}%",
                trigger_date=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            
            self.db.add(alert)
            alerts.append(alert)
        
        self.db.commit()
        return alerts
    
    def check_all_alerts(self) -> Dict[str, List[Alert]]:
        """
        Exécute toutes les vérifications d'alertes
        
        Returns:
            Dictionnaire des alertes par type
        """
        return {
            'guarantee_expiry': self.check_guarantee_expiry(),
            'stage_delays': self.check_stage_delays(),
            'market_delays': self.check_market_delays(),
            'budget_overrun': self.check_budget_overrun()
        }
    
    def get_active_alerts(self, user_id: int = None) -> List[Alert]:
        """
        Récupère les alertes actives
        
        Args:
            user_id: ID de l'utilisateur (optionnel pour filtrer)
            
        Returns:
            Liste des alertes actives
        """
        query = self.db.query(Alert).filter(
            Alert.status == AlertStatus.ACTIVE
        )
        
        if user_id:
            # Filtrer par les marchés accessibles à l'utilisateur
            # (à implémenter selon les permissions)
            pass
        
        return query.order_by(Alert.trigger_date.desc()).all()
    
    def acknowledge_alert(self, alert_id: int, user_id: int) -> Alert:
        """
        Acquitte une alerte
        
        Args:
            alert_id: ID de l'alerte
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de Alert mise à jour
        """
        alert = self.db.query(Alert).filter(
            Alert.id == alert_id
        ).first()
        
        if not alert:
            raise ValueError("Alerte non trouvée")
        
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.resolved_by = user_id
        alert.resolved_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(alert)
        
        return alert
    
    def resolve_alert(self, alert_id: int, user_id: int, resolution_notes: str = None) -> Alert:
        """
        Résout une alerte
        
        Args:
            alert_id: ID de l'alerte
            user_id: ID de l'utilisateur
            resolution_notes: Notes de résolution
            
        Returns:
            Instance de Alert résolue
        """
        alert = self.db.query(Alert).filter(
            Alert.id == alert_id
        ).first()
        
        if not alert:
            raise ValueError("Alerte non trouvée")
        
        alert.status = AlertStatus.RESOLVED
        alert.resolved_by = user_id
        alert.resolved_at = datetime.utcnow()
        alert.resolution_notes = resolution_notes
        
        self.db.commit()
        self.db.refresh(alert)
        
        return alert
    
    def dismiss_alert(self, alert_id: int, user_id: int) -> Alert:
        """
        Ignore une alerte
        
        Args:
            alert_id: ID de l'alerte
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de Alert ignorée
        """
        alert = self.db.query(Alert).filter(
            Alert.id == alert_id
        ).first()
        
        if not alert:
            raise ValueError("Alerte non trouvée")
        
        alert.status = AlertStatus.DISMISSED
        alert.resolved_by = user_id
        alert.resolved_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(alert)
        
        return alert
    
    def create_alert_rule(self, rule_data: dict, user_id: int) -> AlertRule:
        """
        Crée une règle d'alerte
        
        Args:
            rule_data: Données de la règle
            user_id: ID de l'utilisateur créateur
            
        Returns:
            Instance de AlertRule créée
        """
        rule = AlertRule(
            alert_type=rule_data['alert_type'],
            severity=rule_data['severity'],
            condition=rule_data['condition'],
            threshold_days=rule_data.get('threshold_days'),
            threshold_percentage=rule_data.get('threshold_percentage'),
            title_template=rule_data['title_template'],
            message_template=rule_data['message_template'],
            is_active=rule_data.get('is_active', True),
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        
        return rule
    
    def get_alert_summary(self) -> Dict:
        """
        Récupère un résumé des alertes
        
        Returns:
            Dictionnaire du résumé
        """
        active_alerts = self.db.query(Alert).filter(
            Alert.status == AlertStatus.ACTIVE
        ).count()
        
        acknowledged_alerts = self.db.query(Alert).filter(
            Alert.status == AlertStatus.ACKNOWLEDGED
        ).count()
        
        critical_alerts = self.db.query(Alert).filter(
            and_(
                Alert.status == AlertStatus.ACTIVE,
                Alert.severity == AlertSeverity.CRITICAL
            )
        ).count()
        
        return {
            'active_count': active_alerts,
            'acknowledged_count': acknowledged_alerts,
            'critical_count': critical_alerts,
            'total_count': active_alerts + acknowledged_alerts
        }


def get_alert_service(db: Session) -> AlertService:
    """
    Factory pour créer une instance du service d'alertes
    
    Args:
        db: Session de base de données
        
    Returns:
        Instance de AlertService
    """
    return AlertService(db)
