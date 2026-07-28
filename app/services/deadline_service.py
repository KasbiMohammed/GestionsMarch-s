"""
Service de gestion des délais réglementaires
Module dédié avec moteur générique de calcul des délais
Conforme au Décret n°2-22-431 du 8 mars 2023
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.deadline import (
    Deadline, DeadlineSettings, DeadlineAlert, DeadlineNotification,
    DeadlineType, AlertLevel, DeadlineStatus, NotificationStatus
)
from app.models.market import Market
from app.models.offer_management import Offer


class DeadlineService:
    """Service pour la gestion intelligente des délais réglementaires"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============================================
    # MOTEUR GÉNÉRIQUE DE CALCUL DES DÉLAIS
    # ============================================
    
    def calculate_deadline_status(self, deadline: Deadline) -> Dict:
        """
        Calcule automatiquement le statut d'un délai
        Moteur générique basé sur les paramètres configurés en base de données
        
        Args:
            deadline: Instance du délai
            
        Returns:
            Dictionnaire avec les calculs
        """
        today = date.today()
        due_date = deadline.due_date
        
        # Calcul des jours restants
        if due_date >= today:
            days_remaining = (due_date - today).days
            days_overdue = 0
        else:
            days_remaining = 0
            days_overdue = (today - due_date).days
        
        # Récupérer les paramètres configurés pour ce type de délai
        settings = self.db.query(DeadlineSettings).filter(
            DeadlineSettings.deadline_type == deadline.deadline_type
        ).first()
        
        # Déterminer le niveau d'alerte selon les paramètres configurés
        alert_level = self._determine_alert_level(days_remaining, days_overdue, settings)
        
        # Déterminer le statut
        status = self._determine_status(days_remaining, days_overdue, deadline.completed_date)
        
        return {
            'days_remaining': days_remaining,
            'days_overdue': days_overdue,
            'alert_level': alert_level,
            'status': status
        }
    
    def _determine_alert_level(self, days_remaining: int, days_overdue: int, 
                               settings: Optional[DeadlineSettings]) -> AlertLevel:
        """
        Détermine le niveau d'alerte selon les paramètres configurés en base de données
        
        Args:
            days_remaining: Jours restants avant l'échéance
            days_overdue: Jours de retard
            settings: Paramètres configurés pour ce type de délai
            
        Returns:
            Niveau d'alerte
        """
        # Si dépassé
        if days_overdue > 0:
            return AlertLevel.DEPASSE
        
        # Si pas de paramètres configurés, utiliser des valeurs par défaut
        if not settings:
            if days_remaining <= 3:
                return AlertLevel.CRITIQUE
            elif days_remaining <= 7:
                return AlertLevel.IMPORTANT
            elif days_remaining <= 15:
                return AlertLevel.ATTENTION
            else:
                return AlertLevel.NORMAL
        
        # Utiliser les paramètres configurés en base de données
        if days_remaining <= settings.critique:
            return AlertLevel.CRITIQUE
        elif days_remaining <= settings.j3:
            return AlertLevel.IMPORTANT
        elif days_remaining <= settings.j2:
            return AlertLevel.ATTENTION
        elif days_remaining <= settings.j1:
            return AlertLevel.NORMAL
        else:
            return AlertLevel.NORMAL
    
    def _determine_status(self, days_remaining: int, days_overdue: int, 
                         completed_date: Optional[date]) -> DeadlineStatus:
        """
        Détermine le statut du délai
        
        Args:
            days_remaining: Jours restants
            days_overdue: Jours de retard
            completed_date: Date de complétion
            
        Returns:
            Statut du délai
        """
        if completed_date:
            return DeadlineStatus.TERMINE
        elif days_overdue > 0:
            return DeadlineStatus.DEPASSE
        else:
            return DeadlineStatus.ACTIF
    
    def update_deadline_calculations(self, deadline_id: int) -> Deadline:
        """
        Met à jour les calculs d'un délai et le niveau d'alerte
        
        Args:
            deadline_id: ID du délai
            
        Returns:
            Délai mis à jour
        """
        deadline = self.db.query(Deadline).filter(Deadline.id == deadline_id).first()
        if not deadline:
            raise ValueError("Délai non trouvé")
        
        # Calculer le statut
        calculations = self.calculate_deadline_status(deadline)
        
        # Mettre à jour le délai
        deadline.days_remaining = calculations['days_remaining']
        deadline.days_overdue = calculations['days_overdue']
        deadline.alert_level = calculations['alert_level']
        deadline.status = calculations['status']
        deadline.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(deadline)
        
        # Générer une alerte si le niveau a changé
        self._check_and_create_alert(deadline)
        
        return deadline
    
    def _check_and_create_alert(self, deadline: Deadline):
        """
        Vérifie si une alerte doit être créée pour ce délai
        
        Args:
            deadline: Délai à vérifier
        """
        # Ne pas créer d'alerte si le niveau est NORMAL
        if deadline.alert_level == AlertLevel.NORMAL:
            return
        
        # Vérifier si une alerte du même niveau existe déjà aujourd'hui
        today = datetime.utcnow().date()
        existing_alert = self.db.query(DeadlineAlert).filter(
            and_(
                DeadlineAlert.deadline_id == deadline.id,
                DeadlineAlert.alert_level == deadline.alert_level,
                DeadlineAlert.alert_date >= datetime.utcnow().replace(hour=0, minute=0, second=0)
            )
        ).first()
        
        if existing_alert:
            return
        
        # Créer une nouvelle alerte
        alert = DeadlineAlert(
            deadline_id=deadline.id,
            alert_level=deadline.alert_level,
            message=self._generate_alert_message(deadline)
        )
        self.db.add(alert)
        self.db.commit()
        
        # Créer une notification
        self._create_notification(deadline, alert)
    
    def _generate_alert_message(self, deadline: Deadline) -> str:
        """Génère un message d'alerte"""
        level_messages = {
            AlertLevel.ATTENTION: f"Attention: Le délai '{deadline.title}' arrive à échéance dans {deadline.days_remaining} jours.",
            AlertLevel.IMPORTANT: f"Important: Le délai '{deadline.title}' arrive à échéance dans {deadline.days_remaining} jours.",
            AlertLevel.CRITIQUE: f"CRITIQUE: Le délai '{deadline.title}' arrive à échéance dans {deadline.days_remaining} jours!",
            AlertLevel.DEPASSE: f"DÉPASSÉ: Le délai '{deadline.title}' est dépassé de {deadline.days_overdue} jours!"
        }
        return level_messages.get(deadline.alert_level, f"Délai: {deadline.title}")
    
    def _create_notification(self, deadline: Deadline, alert: DeadlineAlert):
        """Crée une notification pour les utilisateurs concernés"""
        # TODO: Implémenter la logique de notification aux utilisateurs appropriés
        # Pour l'instant, on peut créer une notification générique
        notification = DeadlineNotification(
            deadline_id=deadline.id,
            user_id=1,  # À adapter: ID de l'utilisateur administrateur ou responsable
            title=f"Alerte délai: {deadline.title}",
            message=alert.message,
            notification_type="dashboard"
        )
        self.db.add(notification)
        self.db.commit()
    
    # ============================================
    # CRUD DES DÉLAIS
    # ============================================
    
    def create_deadline(self, deadline_data: Dict) -> Deadline:
        """
        Crée un nouveau délai réglementaire
        
        Args:
            deadline_data: Données du délai
            
        Returns:
            Délai créé
        """
        deadline = Deadline(
            deadline_type=deadline_data.get('deadline_type'),
            market_id=deadline_data.get('market_id'),
            planning_id=deadline_data.get('planning_id'),
            offer_id=deadline_data.get('offer_id'),
            start_date=deadline_data.get('start_date'),
            due_date=deadline_data.get('due_date'),
            title=deadline_data.get('title'),
            description=deadline_data.get('description'),
            reference=deadline_data.get('reference'),
            created_by=deadline_data.get('created_by')
        )
        
        self.db.add(deadline)
        self.db.commit()
        self.db.refresh(deadline)
        
        # Calculer automatiquement le statut initial
        self.update_deadline_calculations(deadline.id)
        
        return deadline
    
    def update_deadline(self, deadline_id: int, deadline_data: Dict) -> Deadline:
        """
        Met à jour un délai
        
        Args:
            deadline_id: ID du délai
            deadline_data: Nouvelles données
            
        Returns:
            Délai mis à jour
        """
        deadline = self.db.query(Deadline).filter(Deadline.id == deadline_id).first()
        if not deadline:
            raise ValueError("Délai non trouvé")
        
        # Mise à jour des champs
        for field, value in deadline_data.items():
            if hasattr(deadline, field) and field != 'id':
                setattr(deadline, field, value)
        
        deadline.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(deadline)
        
        # Recalculer le statut
        self.update_deadline_calculations(deadline.id)
        
        return deadline
    
    def get_deadline(self, deadline_id: int) -> Optional[Deadline]:
        """Récupère un délai par son ID"""
        return self.db.query(Deadline).filter(Deadline.id == deadline_id).first()
    
    def get_deadlines_by_market(self, market_id: int) -> List[Deadline]:
        """Récupère tous les délais d'un marché"""
        return self.db.query(Deadline).filter(
            Deadline.market_id == market_id
        ).order_by(Deadline.due_date).all()
    
    def get_deadlines_by_type(self, deadline_type: DeadlineType) -> List[Deadline]:
        """Récupère tous les délais d'un type donné"""
        return self.db.query(Deadline).filter(
            Deadline.deadline_type == deadline_type
        ).order_by(Deadline.due_date).all()
    
    def delete_deadline(self, deadline_id: int) -> bool:
        """Supprime un délai"""
        deadline = self.db.query(Deadline).filter(Deadline.id == deadline_id).first()
        if not deadline:
            return False
        
        self.db.delete(deadline)
        self.db.commit()
        return True
    
    # ============================================
    # GESTION DES PARAMÈTRES
    # ============================================
    
    def get_settings(self, deadline_type: Optional[DeadlineType] = None) -> List[DeadlineSettings]:
        """
        Récupère les paramètres de délais
        
        Args:
            deadline_type: Type de délai spécifique (optionnel)
            
        Returns:
            Liste des paramètres
        """
        query = self.db.query(DeadlineSettings)
        if deadline_type:
            query = query.filter(DeadlineSettings.deadline_type == deadline_type)
        return query.order_by(DeadlineSettings.type_name).all()
    
    def update_settings(self, settings_id: int, settings_data: Dict) -> DeadlineSettings:
        """
        Met à jour les paramètres d'un type de délai
        
        Args:
            settings_id: ID des paramètres
            settings_data: Nouvelles valeurs
            
        Returns:
            Paramètres mis à jour
        """
        settings = self.db.query(DeadlineSettings).filter(
            DeadlineSettings.id == settings_id
        ).first()
        if not settings:
            raise ValueError("Paramètres non trouvés")
        
        for field, value in settings_data.items():
            if hasattr(settings, field) and field != 'id':
                setattr(settings, field, value)
        
        settings.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(settings)
        
        # Recalculer tous les délais de ce type
        self.recalculate_deadlines_by_type(settings.deadline_type)
        
        return settings
    
    def recalculate_deadlines_by_type(self, deadline_type: DeadlineType):
        """
        Recalcule tous les délais d'un type donné après modification des paramètres
        
        Args:
            deadline_type: Type de délai
        """
        deadlines = self.get_deadlines_by_type(deadline_type)
        for deadline in deadlines:
            self.update_deadline_calculations(deadline.id)
    
    # ============================================
    # STATISTIQUES ET RAPPORTS
    # ============================================
    
    def get_deadline_statistics(self) -> Dict:
        """
        Récupère les statistiques globales des délais
        
        Returns:
            Dictionnaire de statistiques
        """
        total = self.db.query(Deadline).count()
        
        overdue = self.db.query(Deadline).filter(
            Deadline.status == DeadlineStatus.DEPASSE
        ).count()
        
        critical = self.db.query(Deadline).filter(
            Deadline.alert_level == AlertLevel.CRITIQUE
        ).count()
        
        important = self.db.query(Deadline).filter(
            Deadline.alert_level == AlertLevel.IMPORTANT
        ).count()
        
        attention = self.db.query(Deadline).filter(
            Deadline.alert_level == AlertLevel.ATTENTION
        ).count()
        
        completed = self.db.query(Deadline).filter(
            Deadline.status == DeadlineStatus.TERMINE
        ).count()
        
        return {
            'total': total,
            'overdue': overdue,
            'critical': critical,
            'important': important,
            'attention': attention,
            'normal': total - overdue - critical - important - attention - completed,
            'completed': completed
        }
    
    def get_upcoming_deadlines(self, days: int = 30) -> List[Deadline]:
        """
        Récupère les délais à venir dans les X jours
        
        Args:
            days: Nombre de jours à venir
            
        Returns:
            Liste des délais à venir
        """
        future_date = date.today() + timedelta(days=days)
        
        return self.db.query(Deadline).filter(
            and_(
                Deadline.due_date >= date.today(),
                Deadline.due_date <= future_date,
                Deadline.status == DeadlineStatus.ACTIF
            )
        ).order_by(Deadline.due_date).all()
    
    def get_overdue_deadlines(self) -> List[Deadline]:
        """Récupère tous les délais dépassés"""
        return self.db.query(Deadline).filter(
            Deadline.status == DeadlineStatus.DEPASSE
        ).order_by(desc(Deadline.days_overdue)).all()
    
    def get_critical_deadlines(self) -> List[Deadline]:
        """Récupère tous les délais critiques"""
        return self.db.query(Deadline).filter(
            and_(
                Deadline.alert_level == AlertLevel.CRITIQUE,
                Deadline.status == DeadlineStatus.ACTIF
            )
        ).order_by(Deadline.due_date).all()
    
    def get_deadlines_for_calendar(self, start_date: date, end_date: date) -> List[Dict]:
        """
        Récupère les délais pour une période donnée (pour le calendrier)
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            
        Returns:
            Liste des délais formatés pour le calendrier
        """
        deadlines = self.db.query(Deadline).filter(
            and_(
                Deadline.due_date >= start_date,
                Deadline.due_date <= end_date
            )
        ).all()
        
        calendar_events = []
        for deadline in deadlines:
            calendar_events.append({
                'id': deadline.id,
                'title': deadline.title,
                'start': deadline.due_date.isoformat(),
                'backgroundColor': self._get_color_for_alert_level(deadline.alert_level),
                'borderColor': self._get_color_for_alert_level(deadline.alert_level),
                'extendedProps': {
                    'deadline_type': deadline.deadline_type.value,
                    'status': deadline.status.value,
                    'days_remaining': deadline.days_remaining,
                    'market_id': deadline.market_id
                }
            })
        
        return calendar_events
    
    def _get_color_for_alert_level(self, alert_level: AlertLevel) -> str:
        """Retourne la couleur CSS pour un niveau d'alerte"""
        colors = {
            AlertLevel.NORMAL: '#28a745',      # Vert
            AlertLevel.ATTENTION: '#ffc107',   # Jaune
            AlertLevel.IMPORTANT: '#fd7e14',   # Orange
            AlertLevel.CRITIQUE: '#dc3545',    # Rouge
            AlertLevel.DEPASSE: '#6c757d'      # Gris
        }
        return colors.get(alert_level, '#28a745')
    
    # ============================================
    # GESTION DES ALERTES ET NOTIFICATIONS
    # ============================================
    
    def get_alerts(self, acknowledged: Optional[bool] = None) -> List[DeadlineAlert]:
        """
        Récupère les alertes
        
        Args:
            acknowledged: Filtre sur le statut de reconnaissance
            
        Returns:
            Liste des alertes
        """
        query = self.db.query(DeadlineAlert).order_by(desc(DeadlineAlert.alert_date))
        if acknowledged is not None:
            query = query.filter(DeadlineAlert.acknowledged == acknowledged)
        return query.all()
    
    def acknowledge_alert(self, alert_id: int, user_id: int) -> bool:
        """
        Reconnaît une alerte
        
        Args:
            alert_id: ID de l'alerte
            user_id: ID de l'utilisateur
            
        Returns:
            True si succès
        """
        alert = self.db.query(DeadlineAlert).filter(DeadlineAlert.id == alert_id).first()
        if not alert:
            return False
        
        alert.acknowledged = True
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def get_notifications(self, user_id: int, status: Optional[NotificationStatus] = None) -> List[DeadlineNotification]:
        """
        Récupère les notifications d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            status: Filtre sur le statut
            
        Returns:
            Liste des notifications
        """
        query = self.db.query(DeadlineNotification).filter(
            DeadlineNotification.user_id == user_id
        ).order_by(desc(DeadlineNotification.created_at))
        
        if status:
            query = query.filter(DeadlineNotification.status == status)
        
        return query.all()
    
    def mark_notification_read(self, notification_id: int) -> bool:
        """
        Marque une notification comme lue
        
        Args:
            notification_id: ID de la notification
            
        Returns:
            True si succès
        """
        notification = self.db.query(DeadlineNotification).filter(
            DeadlineNotification.id == notification_id
        ).first()
        if not notification:
            return False
        
        notification.status = NotificationStatus.LU
        notification.read_date = datetime.utcnow()
        
        self.db.commit()
        return True


def get_deadline_service(db: Session) -> DeadlineService:
    """
    Factory pour créer une instance du service de délais
    
    Args:
        db: Session de base de données
        
    Returns:
        Instance de DeadlineService
    """
    return DeadlineService(db)
