"""
Service de tableaux de bord
Module 12: Tableaux de bord - KPIs Président/DG, cartographie projets
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, sum as sql_sum

from app.models.market import Market, MarketStatus
from app.models.execution import Payment, Amendment
from app.models.annual_planning import AnnualPlanning, ServiceNeed
from app.models.stage import Stage


class DashboardService:
    """Service pour les tableaux de bord et KPIs"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_president_dashboard(self) -> Dict:
        """
        Récupère le tableau de bord du Président
        
        Returns:
            Dictionnaire des KPIs pour le Président
        """
        current_year = datetime.utcnow().year
        
        # Statistiques générales
        total_markets = self.db.query(Market).filter(
            Market.is_deleted == False
        ).count()
        
        total_budget = self.db.query(func.sum(Market.budget)).filter(
            Market.is_deleted == False
        ).scalar() or 0
        
        total_engaged = self.db.query(func.sum(Market.final_amount)).filter(
            and_(
                Market.is_deleted == False,
                Market.final_amount.isnot(None)
            )
        ).scalar() or 0
        
        # Marchés en cours
        markets_in_progress = self.db.query(Market).filter(
            and_(
                Market.is_deleted == False,
                Market.status == MarketStatus.EN_COURS
            )
        ).count()
        
        # Marchés terminés
        markets_completed = self.db.query(Market).filter(
            and_(
                Market.is_deleted == False,
                Market.status == MarketStatus.TERMINE
            )
        ).count()
        
        # Marchés en retard
        markets_late = self.db.query(Market).filter(
            and_(
                Market.is_deleted == False,
                Market.status == MarketStatus.EN_RETARD
            )
        ).count()
        
        # Paiements
        total_paid = self.db.query(func.sum(Payment.amount)).filter(
            Payment.paid == True
        ).scalar() or 0
        
        # Répartition par service
        by_service = self._get_markets_by_service()
        
        # Répartition par entreprise
        by_company = self._get_markets_by_company()
        
        # Délais moyens
        average_delays = self._get_average_delays()
        
        # Évolution annuelle
        annual_evolution = self._get_annual_evolution(current_year)
        
        return {
            'total_markets': total_markets,
            'total_budget': total_budget,
            'total_engaged': total_engaged,
            'total_paid': total_paid,
            'markets_in_progress': markets_in_progress,
            'markets_completed': markets_completed,
            'markets_late': markets_late,
            'by_service': by_service,
            'by_company': by_company,
            'average_delays': average_delays,
            'annual_evolution': annual_evolution,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def get_director_dashboard(self) -> Dict:
        """
        Récupère le tableau de bord du Directeur Général
        
        Returns:
            Dictionnaire des KPIs pour le DG
        """
        current_year = datetime.utcnow().year
        
        # Statistiques détaillées
        markets_by_status = self._get_markets_by_status()
        
        # Budget par type de marché
        budget_by_type = self._get_budget_by_type()
        
        # Avenants
        amendments_count = self.db.query(Amendment).count()
        total_amendment_amount = self.db.query(func.sum(Amendment.amount_difference)).filter(
            Amendment.amount_difference.isnot(None)
        ).scalar() or 0
        
        # Planification annuelle
        planning_stats = self._get_planning_statistics(current_year)
        
        # Alertes actives
        from app.models.alerts import Alert, AlertStatus
        active_alerts = self.db.query(Alert).filter(
            Alert.status == AlertStatus.ACTIVE
        ).count()
        
        # Projets en cours par zone (cartographie)
        projects_by_location = self._get_projects_by_location()
        
        return {
            'markets_by_status': markets_by_status,
            'budget_by_type': budget_by_type,
            'amendments_count': amendments_count,
            'total_amendment_amount': total_amendment_amount,
            'planning_statistics': planning_stats,
            'active_alerts': active_alerts,
            'projects_by_location': projects_by_location,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def get_service_dashboard(self, service_id: int) -> Dict:
        """
        Récupère le tableau de bord d'un service
        
        Args:
            service_id: ID du service
            
        Returns:
            Dictionnaire des KPIs pour le service
        """
        # Marchés du service
        service_markets = self.db.query(Market).filter(
            and_(
                Market.is_deleted == False,
                Market.responsible_service_id == service_id
            )
        ).all()
        
        total_markets = len(service_markets)
        total_budget = sum(m.budget for m in service_markets if m.budget)
        
        # Étapes en retard
        late_stages = self.db.query(Stage).join(Market).filter(
            and_(
                Market.responsible_service_id == service_id,
                Stage.is_late == True
            )
        ).count()
        
        # Besoins du service
        service_needs = self.db.query(ServiceNeed).filter(
            ServiceNeed.service_id == service_id
        ).all()
        
        total_needs = len(service_needs)
        realized_needs = len([n for n in service_needs if n.is_realized])
        
        return {
            'total_markets': total_markets,
            'total_budget': total_budget,
            'late_stages': late_stages,
            'total_needs': total_needs,
            'realized_needs': realized_needs,
            'realization_rate': (realized_needs / total_needs * 100) if total_needs > 0 else 0,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _get_markets_by_service(self) -> Dict:
        """Récupère la répartition des marchés par service"""
        results = self.db.query(
            Market.responsible_service,
            func.count(Market.id),
            func.sum(Market.budget)
        ).filter(
            Market.is_deleted == False
        ).group_by(Market.responsible_service).all()
        
        return {
            service: {'count': count, 'budget': budget or 0}
            for service, count, budget in results
        }
    
    def _get_markets_by_company(self) -> Dict:
        """Récupère la répartition des marchés par entreprise"""
        results = self.db.query(
            Market.awardee,
            func.count(Market.id),
            func.sum(Market.final_amount)
        ).filter(
            and_(
                Market.is_deleted == False,
                Market.awardee.isnot(None)
            )
        ).group_by(Market.awardee).all()
        
        return {
            company: {'count': count, 'amount': amount or 0}
            for company, count, amount in results
        }
    
    def _get_average_delays(self) -> Dict:
        """Calcule les délais moyens"""
        stages = self.db.query(Stage).filter(
            Stage.is_late == True
        ).all()
        
        if not stages:
            return {'average_delay_days': 0, 'max_delay_days': 0}
        
        delays = [s.delay_days for s in stages if s.delay_days]
        
        return {
            'average_delay_days': sum(delays) / len(delays) if delays else 0,
            'max_delay_days': max(delays) if delays else 0
        }
    
    def _get_annual_evolution(self, year: int) -> Dict:
        """Récupère l'évolution annuelle"""
        months = []
        for month in range(1, 13):
            month_start = datetime(year, month, 1)
            month_end = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
            
            count = self.db.query(Market).filter(
                and_(
                    Market.is_deleted == False,
                    Market.created_at >= month_start,
                    Market.created_at < month_end
                )
            ).count()
            
            months.append({
                'month': month,
                'count': count
            })
        
        return months
    
    def _get_markets_by_status(self) -> Dict:
        """Récupère les marchés par statut"""
        results = self.db.query(
            Market.status,
            func.count(Market.id)
        ).filter(
            Market.is_deleted == False
        ).group_by(Market.status).all()
        
        return {status.value: count for status, count in results}
    
    def _get_budget_by_type(self) -> Dict:
        """Récupère le budget par type de marché"""
        results = self.db.query(
            Market.type,
            func.count(Market.id),
            func.sum(Market.budget)
        ).filter(
            Market.is_deleted == False
        ).group_by(Market.type).all()
        
        return {
            market_type.value: {'count': count, 'budget': budget or 0}
            for market_type, count, budget in results
        }
    
    def _get_planning_statistics(self, year: int) -> Dict:
        """Récupère les statistiques de planification"""
        plannings = self.db.query(AnnualPlanning).filter(
            AnnualPlanning.year == year
        ).all()
        
        total_budget = sum(p.total_budget for p in plannings)
        consumed_budget = sum(p.consumed_budget for p in plannings)
        
        return {
            'total_plannings': len(plannings),
            'total_budget': total_budget,
            'consumed_budget': consumed_budget,
            'budget_consumption_rate': (consumed_budget / total_budget * 100) if total_budget > 0 else 0
        }
    
    def _get_projects_by_location(self) -> Dict:
        """Récupère les projets par localisation (cartographie)"""
        # Dans une implémentation réelle, on utiliserait des coordonnées GPS
        # Ici on utilise le champ owner (commune) comme localisation
        results = self.db.query(
            Market.owner,
            func.count(Market.id),
            func.sum(Market.budget)
        ).filter(
            Market.is_deleted == False
        ).group_by(Market.owner).all()
        
        return {
            location: {'count': count, 'budget': budget or 0}
            for location, count, budget in results
        }
    
    def get_real_time_kpis(self) -> Dict:
        """
        Récupère les KPIs en temps réel
        
        Returns:
            Dictionnaire des KPIs en temps réel
        """
        from app.models.alerts import Alert, AlertStatus
        
        # Alertes critiques
        critical_alerts = self.db.query(Alert).filter(
            and_(
                Alert.status == AlertStatus.ACTIVE,
                Alert.severity == 'critique'
            )
        ).count()
        
        # Marchés à surveiller
        markets_to_watch = self.db.query(Market).filter(
            Market.status.in_([MarketStatus.EN_RETARD, MarketStatus.EN_ATTENTE])
        ).count()
        
        # Échéances à venir (7 jours)
        from datetime import timedelta
        next_week = datetime.utcnow() + timedelta(days=7)
        
        upcoming_deadlines = self.db.query(Stage).filter(
            and_(
                Stage.planned_date >= datetime.utcnow(),
                Stage.planned_date <= next_week,
                Stage.status != 'termine'
            )
        ).count()
        
        return {
            'critical_alerts': critical_alerts,
            'markets_to_watch': markets_to_watch,
            'upcoming_deadlines': upcoming_deadlines,
            'last_updated': datetime.utcnow().isoformat()
        }


def get_dashboard_service(db: Session) -> DashboardService:
    """
    Factory pour créer une instance du service de tableau de bord
    
    Args:
        db: Session de base de données
        
    Returns:
        Instance de DashboardService
    """
    return DashboardService(db)
