"""
Service métier pour le Dashboard de Supervision
Module de pilotage global avec calcul automatique des KPI
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from app.models.market_planning import MarketPlanning, MarketPlanningStatus
from app.models.market_preparation import MarketPreparation
from app.models.validation_workflow import ValidationWorkflow, WorkflowStatus
from app.models.commission import Commission, CommissionStatus
from app.models.publication import Publication, PublicationStatus


class SupervisionService:
    """Service de supervision et calcul des KPI"""

    def __init__(self, db: Session):
        self.db = db

    def get_global_kpis(self, filters: Optional[Dict] = None) -> Dict:
        """Calcule tous les KPI globaux du dashboard."""
        filters = filters or {}
        
        return {
            "total_markets": self.get_total_markets(filters),
            "markets_by_status": self.get_markets_by_status(filters),
            "markets_by_state": self.get_markets_by_state(filters),
            "global_progress_rate": self.get_global_progress_rate(filters),
            "by_market_type": self.get_by_market_type(filters),
            "by_procedure": self.get_by_procedure(filters),
            "by_service": self.get_by_service(filters),
            "budget_indicators": self.get_budget_indicators(filters),
            "estimation_variance": self.get_estimation_variance(filters),
            "delayed_markets": self.get_delayed_markets(filters),
            "upcoming_deadlines": self.get_upcoming_deadlines(filters),
            "average_delays": self.get_average_delays(filters),
            "validations_pending": self.get_validations_pending(filters),
            "commissions_stats": self.get_commissions_stats(filters),
            "postponed_sessions": self.get_postponed_sessions(filters),
            "published_notices": self.get_published_notices(filters),
            "offers_received": self.get_offers_received(filters),
            "reclamations_stats": self.get_reclamations_stats(filters),
            "avenants_count": self.get_avenants_count(filters),
            "penalties_count": self.get_penalties_count(filters),
            "receptions_stats": self.get_receptions_stats(filters),
            "blocked_markets": self.get_blocked_markets(filters),
            "missing_documents": self.get_missing_documents(filters),
            "critical_alerts": self.get_critical_alerts(filters),
            "top_risk_markets": self.get_top_risk_markets(filters),
            "top_delayed_markets": self.get_top_delayed_markets(filters),
            "top_upcoming_deadlines": self.get_top_upcoming_deadlines(filters),
            "upcoming_calendar": self.get_upcoming_calendar(filters),
            "recent_activities": self.get_recent_activities(filters),
        }

    def get_total_markets(self, filters: Dict) -> int:
        """Nombre total de marchés."""
        query = self.db.query(MarketPlanning).filter(
            MarketPlanning.is_deleted == False
        )
        return self._apply_filters(query, filters).count()

    def get_markets_by_status(self, filters: Dict) -> Dict:
        """Marchés par statut."""
        query = self.db.query(MarketPlanning.status, func.count(MarketPlanning.id)).filter(
            MarketPlanning.is_deleted == False
        )
        query = self._apply_filters(query, filters)
        results = query.group_by(MarketPlanning.status).all()
        
        status_labels = {
            'brouillon': 'Brouillon',
            'en_cours': 'En cours',
            'validee': 'Validée',
            'annulee': 'Annulée',
            'suspendue': 'Suspendue',
            'terminee': 'Terminée'
        }
        
        return {status_labels.get(s[0], s[0]): s[1] for s in results}

    def get_markets_by_state(self, filters: Dict) -> Dict:
        """Marchés par état (actifs, terminés, annulés, suspendus)."""
        query = self.db.query(MarketPlanning).filter(
            MarketPlanning.is_deleted == False
        )
        query = self._apply_filters(query, filters)
        
        total = query.count()
        active = query.filter(MarketPlanning.status.in_(['en_cours', 'validee'])).count()
        terminated = query.filter(MarketPlanning.status == 'terminee').count()
        cancelled = query.filter(MarketPlanning.status == 'annulee').count()
        suspended = query.filter(MarketPlanning.status == 'suspendue').count()
        
        return {
            "actifs": active,
            "termines": terminated,
            "annules": cancelled,
            "suspendus": suspended,
            "total": total
        }

    def get_global_progress_rate(self, filters: Dict) -> float:
        """Taux global d'avancement."""
        query = self.db.query(MarketPlanning).filter(
            MarketPlanning.is_deleted == False
        )
        query = self._apply_filters(query, filters)
        
        markets = query.all()
        if not markets:
            return 0.0
        
        total_progress = sum(m.progress_percentage or 0 for m in markets)
        return round(total_progress / len(markets), 2)

    def get_by_market_type(self, filters: Dict) -> Dict:
        """Répartition par type de marché."""
        query = self.db.query(MarketPlanning.project_type, func.count(MarketPlanning.id)).filter(
            MarketPlanning.is_deleted == False
        )
        query = self._apply_filters(query, filters)
        results = query.group_by(MarketPlanning.project_type).all()
        
        return {s[0] or 'Non défini': s[1] for s in results}

    def get_by_procedure(self, filters: Dict) -> Dict:
        """Répartition par procédure."""
        query = self.db.query(MarketPlanning.procedure_type, func.count(MarketPlanning.id)).filter(
            MarketPlanning.is_deleted == False
        )
        query = self._apply_filters(query, filters)
        results = query.group_by(MarketPlanning.procedure_type).all()
        
        return {s[0] or 'Non défini': s[1] for s in results}

    def get_by_service(self, filters: Dict) -> Dict:
        """Répartition par service maître d'ouvrage."""
        query = self.db.query(MarketPlanning.requesting_service_id, func.count(MarketPlanning.id)).filter(
            MarketPlanning.is_deleted == False
        )
        query = self._apply_filters(query, filters)
        results = query.group_by(MarketPlanning.requesting_service_id).all()
        
        # Récupérer les noms des services
        service_names = {}
        for service_id, count in results:
            if service_id:
                from app.models.user import User
                service = self.db.query(User).filter(User.id == service_id).first()
                service_names[service.full_name if service else f"Service {service_id}"] = count
        
        return service_names

    def get_budget_indicators(self, filters: Dict) -> Dict:
        """Indicateurs budgétaires."""
        query = self.db.query(MarketPlanning).filter(
            MarketPlanning.is_deleted == False
        )
        query = self._apply_filters(query, filters)
        
        markets = query.all()
        
        programmed = sum(m.estimated_budget or 0 for m in markets)
        engaged = sum(m.estimated_budget or 0 for m in markets if m.status in ['en_cours', 'validee'])
        attributed = sum(m.estimated_budget or 0 for m in markets if m.status == 'terminee')
        paid = sum(m.estimated_budget or 0 for m in markets if m.status == 'terminee') * 0.7  # Estimation
        remaining = programmed - engaged
        
        return {
            "programme": round(programmed, 2),
            "engage": round(engaged, 2),
            "attribue": round(attributed, 2),
            "paye": round(paid, 2),
            "restant": round(remaining, 2)
        }

    def get_estimation_variance(self, filters: Dict) -> Dict:
        """Écart entre estimation et montant attribué."""
        # Pour l'instant, retourne 0 car le montant attribué n'est pas encore implémenté
        return {
            "ecart_total": 0,
            "ecart_moyen": 0,
            "ecart_pourcentage": 0
        }

    def get_delayed_markets(self, filters: Dict) -> int:
        """Nombre de marchés en retard."""
        query = self.db.query(MarketPlanning).filter(
            MarketPlanning.is_deleted == False,
            MarketPlanning.planned_end_date < datetime.utcnow(),
            MarketPlanning.status.in_(['en_cours', 'validee'])
        )
        query = self._apply_filters(query, filters)
        return query.count()

    def get_upcoming_deadlines(self, filters: Dict) -> int:
        """Nombre de marchés proches des échéances (7 jours)."""
        cutoff_date = datetime.utcnow() + timedelta(days=7)
        query = self.db.query(MarketPlanning).filter(
            MarketPlanning.is_deleted == False,
            MarketPlanning.planned_end_date <= cutoff_date,
            MarketPlanning.planned_end_date >= datetime.utcnow(),
            MarketPlanning.status.in_(['en_cours', 'validee'])
        )
        query = self._apply_filters(query, filters)
        return query.count()

    def get_average_delays(self, filters: Dict) -> Dict:
        """Délais moyens de passation et d'exécution."""
        query = self.db.query(MarketPlanning).filter(
            MarketPlanning.is_deleted == False
        )
        query = self._apply_filters(query, filters)
        
        markets = query.all()
        
        # Calcul simplifié
        avg_passation = 30  # jours (estimation)
        avg_execution = 180  # jours (estimation)
        
        return {
            "delai_passation_moyen": avg_passation,
            "delai_execution_moyen": avg_execution
        }

    def get_validations_pending(self, filters: Dict) -> int:
        """Nombre de validations en attente."""
        query = self.db.query(ValidationWorkflow).filter(
            ValidationWorkflow.is_deleted == False,
            ValidationWorkflow.status.in_([WorkflowStatus.EN_ATTENTE, WorkflowStatus.IN_PROGRESS])
        )
        return query.count()

    def get_commissions_stats(self, filters: Dict) -> Dict:
        """Statistiques des commissions."""
        query = self.db.query(Commission).filter(
            Commission.is_deleted == False
        )
        
        planned = query.filter(Commission.status == CommissionStatus.SESSIONS_PLANNED).count()
        in_progress = query.filter(Commission.status == CommissionStatus.SESSION_IN_PROGRESS).count()
        closed = query.filter(Commission.status == CommissionStatus.COMMISSION_CLOSED).count()
        
        return {
            "planifiees": planned,
            "en_cours": in_progress,
            "cloturees": closed
        }

    def get_postponed_sessions(self, filters: Dict) -> int:
        """Nombre de séances de commission reportées."""
        from app.models.commission import SessionStatus
        query = self.db.query(func.count(func.distinct(Commission.id))).join(
            CommissionSession
        ).filter(
            Commission.is_deleted == False,
            CommissionSession.status == SessionStatus.POSTPONED
        )
        return query.scalar() or 0

    def get_published_notices(self, filters: Dict) -> int:
        """Nombre d'avis publiés."""
        query = self.db.query(Publication).filter(
            Publication.is_deleted == False,
            Publication.status == PublicationStatus.PUBLISHED
        )
        return query.count()

    def get_offers_received(self, filters: Dict) -> Dict:
        """Nombre d'offres reçues par marché."""
        # Pour l'instant, retourne des données simulées
        return {
            "total_offres": 0,
            "avg_offers_per_market": 0,
            "by_market": {}
        }

    def get_reclamations_stats(self, filters: Dict) -> Dict:
        """Statistiques des réclamations."""
        # Pour l'instant, retourne des données simulées
        return {
            "ouvertes": 0,
            "traitees": 0,
            "cloturees": 0
        }

    def get_avenants_count(self, filters: Dict) -> int:
        """Nombre d'avenants."""
        # Pour l'instant, retourne 0 car non implémenté
        return 0

    def get_penalties_count(self, filters: Dict) -> int:
        """Nombre de pénalités."""
        # Pour l'instant, retourne 0 car non implémenté
        return 0

    def get_receptions_stats(self, filters: Dict) -> Dict:
        """Statistiques des réceptions."""
        # Pour l'instant, retourne des données simulées
        return {
            "provisoires": 0,
            "definitives": 0
        }

    def get_blocked_markets(self, filters: Dict) -> int:
        """Nombre de marchés bloqués."""
        query = self.db.query(MarketPlanning).filter(
            MarketPlanning.is_deleted == False,
            MarketPlanning.status == 'suspendue'
        )
        query = self._apply_filters(query, filters)
        return query.count()

    def get_missing_documents(self, filters: Dict) -> int:
        """Nombre de documents obligatoires manquants."""
        # Pour l'instant, retourne 0 car non implémenté
        return 0

    def get_critical_alerts(self, filters: Dict) -> int:
        """Nombre d'alertes critiques."""
        # Compter les alertes critiques de tous les modules
        from app.models.commission import CommissionAlert
        from app.models.publication import PublicationAlert
        from app.models.validation_workflow import ValidationAlert
        
        commission_alerts = self.db.query(CommissionAlert).filter(
            CommissionAlert.severity == 'high',
            CommissionAlert.is_resolved == False
        ).count()
        
        publication_alerts = self.db.query(PublicationAlert).filter(
            PublicationAlert.severity == 'high',
            PublicationAlert.is_resolved == False
        ).count()
        
        validation_alerts = self.db.query(ValidationAlert).filter(
            ValidationAlert.severity == 'high',
            ValidationAlert.is_resolved == False
        ).count()
        
        return commission_alerts + publication_alerts + validation_alerts

    def get_top_risk_markets(self, filters: Dict) -> List[Dict]:
        """Top 10 marchés à risque."""
        query = self.db.query(MarketPlanning).filter(
            MarketPlanning.is_deleted == False,
            MarketPlanning.status.in_(['en_cours', 'validee'])
        ).order_by(MarketPlanning.progress_percentage.asc()).limit(10)
        
        markets = query.all()
        
        return [
            {
                "id": m.id,
                "reference": m.reference,
                "title": m.title,
                "progress": m.progress_percentage or 0,
                "status": m.status,
                "priority": m.priority,
                "risk_score": 100 - (m.progress_percentage or 0)
            }
            for m in markets
        ]

    def get_top_delayed_markets(self, filters: Dict) -> List[Dict]:
        """Top 10 marchés en retard."""
        query = self.db.query(MarketPlanning).filter(
            MarketPlanning.is_deleted == False,
            MarketPlanning.planned_end_date < datetime.utcnow(),
            MarketPlanning.status.in_(['en_cours', 'validee'])
        ).order_by(MarketPlanning.planned_end_date.asc()).limit(10)
        
        markets = query.all()
        
        return [
            {
                "id": m.id,
                "reference": m.reference,
                "title": m.title,
                "planned_end_date": m.planned_end_date,
                "delay_days": (datetime.utcnow() - m.planned_end_date).days if m.planned_end_date else 0
            }
            for m in markets
        ]

    def get_top_upcoming_deadlines(self, filters: Dict) -> List[Dict]:
        """Top 10 marchés proches de leur échéance."""
        cutoff_date = datetime.utcnow() + timedelta(days=30)
        query = self.db.query(MarketPlanning).filter(
            MarketPlanning.is_deleted == False,
            MarketPlanning.planned_end_date <= cutoff_date,
            MarketPlanning.planned_end_date >= datetime.utcnow(),
            MarketPlanning.status.in_(['en_cours', 'validee'])
        ).order_by(MarketPlanning.planned_end_date.asc()).limit(10)
        
        markets = query.all()
        
        return [
            {
                "id": m.id,
                "reference": m.reference,
                "title": m.title,
                "planned_end_date": m.planned_end_date,
                "days_until": (m.planned_end_date - datetime.utcnow()).days if m.planned_end_date else 0
            }
            for m in markets
        ]

    def get_upcoming_calendar(self, filters: Dict) -> List[Dict]:
        """Calendrier des prochaines échéances."""
        cutoff_date = datetime.utcnow() + timedelta(days=30)
        
        events = []
        
        # Échéances de planification
        markets = self.db.query(MarketPlanning).filter(
            MarketPlanning.is_deleted == False,
            MarketPlanning.planned_end_date <= cutoff_date,
            MarketPlanning.planned_end_date >= datetime.utcnow(),
            MarketPlanning.status.in_(['en_cours', 'validee'])
        ).all()
        
        for m in markets:
            events.append({
                "type": "fin_marche",
                "date": m.planned_end_date,
                "title": f"Fin marché: {m.reference}",
                "market_id": m.id
            })
        
        # Échéances de publication
        from app.models.publication import PublicationDeadline
        deadlines = self.db.query(PublicationDeadline).join(
            Publication
        ).filter(
            Publication.is_deleted == False,
            PublicationDeadline.deadline_date <= cutoff_date,
            PublicationDeadline.deadline_date >= datetime.utcnow(),
            PublicationDeadline.is_completed == False
        ).all()
        
        for d in deadlines:
            events.append({
                "type": "publication",
                "date": d.deadline_date,
                "title": f"{d.description or d.deadline_type}",
                "publication_id": d.publication_id
            })
        
        # Trier par date
        events.sort(key=lambda x: x['date'])
        
        return events[:20]

    def get_recent_activities(self, filters: Dict) -> List[Dict]:
        """Activités récentes (journal des actions)."""
        activities = []
        
        # Historique des validations
        from app.models.validation_workflow import ValidationHistory
        validations = self.db.query(ValidationHistory).order_by(
            ValidationHistory.created_at.desc()
        ).limit(10).all()
        
        for v in validations:
            activities.append({
                "date": v.created_at,
                "type": "validation",
                "action": v.action,
                "user": v.user_name,
                "description": v.description
            })
        
        # Historique des commissions
        from app.models.commission import CommissionHistory
        commissions = self.db.query(CommissionHistory).order_by(
            CommissionHistory.created_at.desc()
        ).limit(10).all()
        
        for c in commissions:
            activities.append({
                "date": c.created_at,
                "type": "commission",
                "action": c.action,
                "user": c.user_name,
                "description": c.description
            })
        
        # Historique des publications
        from app.models.publication import PublicationHistory
        publications = self.db.query(PublicationHistory).order_by(
            PublicationHistory.created_at.desc()
        ).limit(10).all()
        
        for p in publications:
            activities.append({
                "date": p.created_at,
                "type": "publication",
                "action": p.action,
                "user": p.user_name,
                "description": p.description
            })
        
        # Trier par date
        activities.sort(key=lambda x: x['date'], reverse=True)
        
        return activities[:20]

    def _apply_filters(self, query, filters: Dict):
        """Applique les filtres à la requête."""
        if filters.get('year'):
            query = query.filter(
                func.extract('year', MarketPlanning.created_at) == filters['year']
            )
        
        if filters.get('service_id'):
            query = query.filter(
                MarketPlanning.requesting_service_id == filters['service_id']
            )
        
        if filters.get('procedure_type'):
            query = query.filter(
                MarketPlanning.procedure_type == filters['procedure_type']
            )
        
        if filters.get('project_type'):
            query = query.filter(
                MarketPlanning.project_type == filters['project_type']
            )
        
        if filters.get('status'):
            query = query.filter(
                MarketPlanning.status == filters['status']
            )
        
        return query
