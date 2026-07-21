"""
Service de KPIs
Calcul des indicateurs de performance clés
"""

from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract

from app.models.market import Market, MarketStatus
from app.models.stage import Stage, StageStatus
from app.dashboard.statistics import StatisticsService


class KPIService:
    """Service pour le calcul des KPIs"""
    
    def __init__(self, db: Session):
        self.db = db
        self.stats_service = StatisticsService(db)
    
    def get_all_kpis(self) -> Dict:
        """
        Récupère tous les KPIs principaux
        
        Returns:
            Dictionnaire de tous les KPIs
        """
        return {
            'market_kpis': self.get_market_kpis(),
            'stage_kpis': self.get_stage_kpis(),
            'budget_kpis': self.get_budget_kpis(),
            'delay_kpis': self.get_delay_kpis(),
            'efficiency_kpis': self.get_efficiency_kpis()
        }
    
    def get_market_kpis(self) -> Dict:
        """
        Calcule les KPIs liés aux marchés
        
        Returns:
            Dictionnaire de KPIs de marchés
        """
        stats = self.stats_service.get_global_statistics()
        
        total = stats['total_markets']
        completed = stats['by_status'].get('terminé', 0)
        in_progress = stats['by_status'].get('en_cours', 0)
        late = stats['late_markets']
        
        # Taux de complétion
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        # Taux de marchés en retard
        late_rate = (late / total * 100) if total > 0 else 0
        
        # Taux de marchés en cours
        progress_rate = (in_progress / total * 100) if total > 0 else 0
        
        return {
            'total_markets': total,
            'completed_markets': completed,
            'in_progress_markets': in_progress,
            'late_markets': late,
            'completion_rate': round(completion_rate, 2),
            'late_rate': round(late_rate, 2),
            'progress_rate': round(progress_rate, 2)
        }
    
    def get_stage_kpis(self) -> Dict:
        """
        Calcule les KPIs liés aux étapes
        
        Returns:
            Dictionnaire de KPIs d'étapes
        """
        stage_stats = self.stats_service.get_stage_statistics()
        
        total_stages = stage_stats['total_stages']
        completed_stages = stage_stats['by_status'].get('completed', 0)
        late_stages = stage_stats['late_stages']
        avg_progress = stage_stats['average_progress']
        
        # Taux de complétion des étapes
        stage_completion_rate = (completed_stages / total_stages * 100) if total_stages > 0 else 0
        
        # Taux d'étapes en retard
        stage_late_rate = (late_stages / total_stages * 100) if total_stages > 0 else 0
        
        return {
            'total_stages': total_stages,
            'completed_stages': completed_stages,
            'late_stages': late_stages,
            'average_progress': avg_progress,
            'stage_completion_rate': round(stage_completion_rate, 2),
            'stage_late_rate': round(stage_late_rate, 2)
        }
    
    def get_budget_kpis(self) -> Dict:
        """
        Calcule les KPIs budgétaires
        
        Returns:
            Dictionnaire de KPIs budgétaires
        """
        budget_stats = self.stats_service.get_budget_statistics()
        
        total_budget = budget_stats['budget_by_status']
        total_budget_sum = sum(total_budget.values())
        
        engaged_budget = budget_stats['final_total']
        estimated_budget = budget_stats['estimated_total']
        
        # Taux d'engagement budgétaire
        engagement_rate = (engaged_budget / total_budget_sum * 100) if total_budget_sum > 0 else 0
        
        # Écart budgétaire
        budget_variance = budget_stats['budget_variance']
        budget_variance_pct = budget_stats['budget_variance_percentage']
        
        # Budget moyen par marché
        from app.models.market import Market
        avg_budget_per_market = self.db.query(func.avg(Market.budget)).filter(
            Market.is_deleted == False
        ).scalar() or 0
        
        return {
            'total_budget': total_budget_sum,
            'engaged_budget': engaged_budget,
            'remaining_budget': total_budget_sum - engaged_budget,
            'engagement_rate': round(engagement_rate, 2),
            'budget_variance': budget_variance,
            'budget_variance_percentage': budget_variance_pct,
            'average_budget_per_market': round(avg_budget_per_market, 2)
        }
    
    def get_delay_kpis(self) -> Dict:
        """
        Calcule les KPIs liés aux retards
        
        Returns:
            Dictionnaire de KPIs de retards
        """
        delay_stats = self.stats_service.get_delay_statistics()
        
        total_late = delay_stats['total_late_stages']
        avg_delay = delay_stats['average_delay_days']
        
        # Retard maximum
        max_delay = self.db.query(func.max(Stage.delay_days)).filter(
            Stage.is_late == True
        ).scalar() or 0
        
        # Retard médian
        from sqlalchemy import literal_column
        # Pour SQLite, on utilise une approche différente
        all_delays = [s.delay_days for s in self.db.query(Stage).filter(
            Stage.is_late == True
        ).all()]
        
        median_delay = 0
        if all_delays:
            all_delays.sort()
            n = len(all_delays)
            median_delay = all_delays[n // 2] if n % 2 == 1 else (all_delays[n // 2 - 1] + all_delays[n // 2]) / 2
        
        return {
            'total_late_stages': total_late,
            'average_delay_days': round(avg_delay, 2),
            'maximum_delay_days': max_delay,
            'median_delay_days': round(median_delay, 2),
            'delay_distribution': delay_stats['by_delay_range']
        }
    
    def get_efficiency_kpis(self) -> Dict:
        """
        Calcule les KPIs d'efficacité
        
        Returns:
            Dictionnaire de KPIs d'efficacité
        """
        # Durée moyenne des marchés
        avg_duration = self.db.query(
            func.avg(
                func.julianday(Market.actual_end_date) - func.julianday(Market.start_date)
            )
        ).filter(
            and_(
                Market.actual_end_date.isnot(None),
                Market.start_date.isnot(None),
                Market.is_deleted == False
            )
        ).scalar() or 0
        
        # Durée moyenne des étapes
        from app.models.stage import Stage
        avg_stage_duration = self.db.query(
            func.avg(
                func.julianday(Stage.actual_date) - func.julianday(Stage.planned_date)
            )
        ).filter(
            and_(
                Stage.actual_date.isnot(None),
                Stage.planned_date.isnot(None)
            )
        ).scalar() or 0
        
        # Taux de respect des délais
        on_time_markets = self.db.query(func.count(Market.id)).filter(
            and_(
                Market.actual_end_date <= Market.expected_end_date,
                Market.actual_end_date.isnot(None),
                Market.expected_end_date.isnot(None),
                Market.is_deleted == False
            )
        ).scalar() or 0
        
        total_completed = self.db.query(func.count(Market.id)).filter(
            and_(
                Market.status == MarketStatus.TERMINE,
                Market.is_deleted == False
            )
        ).scalar() or 0
        
        on_time_rate = (on_time_markets / total_completed * 100) if total_completed > 0 else 0
        
        return {
            'average_market_duration_days': round(avg_duration, 2),
            'average_stage_duration_days': round(avg_stage_duration, 2),
            'on_time_markets': on_time_markets,
            'total_completed_markets': total_completed,
            'on_time_rate': round(on_time_rate, 2)
        }
    
    def get_alert_kpis(self) -> Dict:
        """
        Calcule les KPIs d'alertes
        
        Returns:
            Dictionnaire de KPIs d'alertes
        """
        from app.services.notification_service import NotificationService
        notification_service = NotificationService(self.db)
        
        upcoming = notification_service.get_upcoming_deadlines(days_ahead=7)
        overdue = notification_service.get_overdue_items()
        critical = notification_service.get_critical_alerts()
        
        return {
            'upcoming_deadlines': len(upcoming),
            'overdue_items': len(overdue),
            'critical_alerts': len(critical),
            'high_urgency': len([u for u in upcoming if u.get('urgency') == 'high']),
            'medium_urgency': len([u for u in upcoming if u.get('urgency') == 'medium']),
            'low_urgency': len([u for u in upcoming if u.get('urgency') == 'low'])
        }
    
    def get_trend_kpis(self, period: str = 'monthly') -> Dict:
        """
        Calcule les KPIs de tendance
        
        Args:
            period: Période d'analyse ('monthly' ou 'yearly')
            
        Returns:
            Dictionnaire de KPIs de tendance
        """
        if period == 'monthly':
            current_year = datetime.now().year
            current_month = datetime.now().month
            
            # Marchés ce mois
            this_month = self.db.query(func.count(Market.id)).filter(
                and_(
                    extract('year', Market.created_at) == current_year,
                    extract('month', Market.created_at) == current_month,
                    Market.is_deleted == False
                )
            ).scalar() or 0
            
            # Marchés le mois dernier
            last_month = current_month - 1 if current_month > 1 else 12
            last_month_year = current_year if current_month > 1 else current_year - 1
            
            last_month_count = self.db.query(func.count(Market.id)).filter(
                and_(
                    extract('year', Market.created_at) == last_month_year,
                    extract('month', Market.created_at) == last_month,
                    Market.is_deleted == False
                )
            ).scalar() or 0
            
            # Taux de croissance
            growth_rate = ((this_month - last_month_count) / last_month_count * 100) if last_month_count > 0 else 0
            
            return {
                'this_period': this_month,
                'last_period': last_month_count,
                'growth_rate': round(growth_rate, 2),
                'trend': 'up' if growth_rate > 0 else 'down' if growth_rate < 0 else 'stable'
            }
        
        else:  # yearly
            current_year = datetime.now().year
            last_year = current_year - 1
            
            this_year = self.db.query(func.count(Market.id)).filter(
                and_(
                    extract('year', Market.created_at) == current_year,
                    Market.is_deleted == False
                )
            ).scalar() or 0
            
            last_year_count = self.db.query(func.count(Market.id)).filter(
                and_(
                    extract('year', Market.created_at) == last_year,
                    Market.is_deleted == False
                )
            ).scalar() or 0
            
            growth_rate = ((this_year - last_year_count) / last_year_count * 100) if last_year_count > 0 else 0
            
            return {
                'this_period': this_year,
                'last_period': last_year_count,
                'growth_rate': round(growth_rate, 2),
                'trend': 'up' if growth_rate > 0 else 'down' if growth_rate < 0 else 'stable'
            }


def get_kpi_service(db: Session) -> KPIService:
    """
    Factory pour créer une instance du service de KPIs
    
    Args:
        db: Session de base de données
        
    Returns:
        Instance de KPIService
    """
    return KPIService(db)
