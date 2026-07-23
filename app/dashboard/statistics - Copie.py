"""
Service de statistiques du dashboard
Gestion des marchés publics
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy import func, and_, extract
from sqlalchemy.orm import Session

from app.models.market import Market, MarketStatus, MarketType
from app.models.stage import Stage, StageStatus
from app.models.market_planning import MarketPlanning


class StatisticsService:
    """Service pour le calcul des statistiques"""

    def __init__(self, db: Session):
        self.db = db


    def get_global_statistics(self) -> Dict:
        """
        Récupère les statistiques globales
        """

        # Total des marchés
        total_markets = self.db.query(
            func.count(Market.id)
        ).scalar() or 0


        # Marchés par statut
        by_status = {}

        for status in MarketStatus:
            count = self.db.query(
                func.count(Market.id)
            ).filter(
                Market.status == status
            ).scalar() or 0

            by_status[status.value] = count



        # Marchés par type
        by_type = {}

        for market_type in MarketType:

            count = self.db.query(
                func.count(Market.id)
            ).filter(
                Market.market_type == market_type
            ).scalar() or 0

            by_type[market_type.value] = count



        # Budget total
        total_budget = self.db.query(
            func.sum(Market.budget)
        ).scalar() or 0



        # Budget engagé
        engaged_budget = self.db.query(
            func.sum(Market.definitive_amount)
        ).filter(
            Market.definitive_amount.isnot(None)
        ).scalar() or 0



        # Marchés en retard
        late_markets = self.db.query(
            func.count(Market.id)
        ).filter(
            Market.status == MarketStatus.EN_RETARD
        ).scalar() or 0



        # Statistiques planification
        total_plannings = self.db.query(
            func.count(MarketPlanning.id)
        ).scalar() or 0


        planning_budget = self.db.query(
            func.sum(MarketPlanning.estimated_budget)
        ).scalar() or 0


        plannings_validated = self.db.query(
            func.count(MarketPlanning.id)
        ).filter(
            MarketPlanning.status == "validee"
        ).scalar() or 0


        plannings_programmed = self.db.query(
            func.count(MarketPlanning.id)
        ).filter(
            MarketPlanning.status == "programmee"
        ).scalar() or 0



        return {

            "total_markets": total_markets,

            "by_status": by_status,

            "by_type": by_type,

            "total_budget": total_budget,

            "engaged_budget": engaged_budget,

            "remaining_budget": total_budget - engaged_budget,

            "late_markets": late_markets,

            "on_time_markets":
                by_status.get("EN_COURS", 0) - late_markets,


            "planning": {

                "total": total_plannings,

                "budget": planning_budget,

                "validated": plannings_validated,

                "programmed": plannings_programmed

            }
        }



    def get_monthly_statistics(self, year: int = None) -> Dict:
        """
        Statistiques mensuelles
        """

        if year is None:
            year = datetime.now().year


        monthly_data = {}


        for month in range(1, 13):

            created_count = self.db.query(
                func.count(Market.id)
            ).filter(
                and_(
                    extract(
                        "year",
                        Market.created_at
                    ) == year,

                    extract(
                        "month",
                        Market.created_at
                    ) == month
                )
            ).scalar() or 0



            completed_count = self.db.query(
                func.count(Market.id)
            ).filter(
                and_(
                    extract(
                        "year",
                        Market.actual_end_date
                    ) == year,

                    extract(
                        "month",
                        Market.actual_end_date
                    ) == month
                )
            ).scalar() or 0



            monthly_budget = self.db.query(
                func.sum(Market.budget)
            ).filter(
                and_(
                    extract(
                        "year",
                        Market.created_at
                    ) == year,

                    extract(
                        "month",
                        Market.created_at
                    ) == month
                )
            ).scalar() or 0



            monthly_data[month] = {

                "created": created_count,

                "completed": completed_count,

                "budget": monthly_budget

            }


        return monthly_data



    def get_yearly_statistics(self, years: int = 5) -> Dict:
        """
        Statistiques annuelles
        """

        current_year = datetime.now().year

        yearly_data = {}


        for year in range(
            current_year - years + 1,
            current_year + 1
        ):


            created_count = self.db.query(
                func.count(Market.id)
            ).filter(
                extract(
                    "year",
                    Market.created_at
                ) == year
            ).scalar() or 0



            yearly_budget = self.db.query(
                func.sum(Market.budget)
            ).filter(
                extract(
                    "year",
                    Market.created_at
                ) == year
            ).scalar() or 0



            yearly_data[year] = {

                "created": created_count,

                "budget": yearly_budget

            }


        return yearly_data

    def get_stage_statistics(self) -> Dict:
        """
        Récupère les statistiques des étapes
        """

        # Total des étapes
        total_stages = self.db.query(
            func.count(Stage.id)
        ).scalar() or 0


        # Étapes par statut
        by_status = {}

        for status in StageStatus:

            count = self.db.query(
                func.count(Stage.id)
            ).filter(
                Stage.status == status
            ).scalar() or 0

            by_status[status.value] = count



        # Étapes en retard
        late_stages = self.db.query(
            func.count(Stage.id)
        ).filter(
            Stage.is_late == True
        ).scalar() or 0



        # Progression moyenne
        avg_progress = self.db.query(
            func.avg(Stage.progress_percentage)
        ).scalar() or 0



        return {

            "total_stages": total_stages,

            "by_status": by_status,

            "late_stages": late_stages,

            "average_progress": round(
                float(avg_progress),
                2
            ),

            "completion_rate": round(
                (
                    by_status.get("completed", 0)
                    /
                    total_stages
                    *
                    100
                )
                if total_stages > 0 else 0,

                2
            )
        }



    def get_delay_statistics(self) -> Dict:
        """
        Statistiques des retards
        """

        delay_ranges = {

            "1-7 jours": 0,

            "8-14 jours": 0,

            "15-30 jours": 0,

            "31-60 jours": 0,

            "+60 jours": 0
        }



        late_stages = self.db.query(
            Stage
        ).filter(
            Stage.is_late == True
        ).all()



        for stage in late_stages:

            delay_days = stage.delay_days or 0


            if delay_days <= 7:

                delay_ranges["1-7 jours"] += 1


            elif delay_days <= 14:

                delay_ranges["8-14 jours"] += 1


            elif delay_days <= 30:

                delay_ranges["15-30 jours"] += 1


            elif delay_days <= 60:

                delay_ranges["31-60 jours"] += 1


            else:

                delay_ranges["+60 jours"] += 1



        avg_delay = self.db.query(
            func.avg(Stage.delay_days)
        ).filter(
            Stage.is_late == True
        ).scalar() or 0



        return {

            "total_late_stages": len(late_stages),

            "by_delay_range": delay_ranges,

            "average_delay_days": round(
                float(avg_delay),
                2
            )
        }





    def get_budget_statistics(self) -> Dict:
        """
        Statistiques budgétaires
        """

        # Budget par type
        budget_by_type = {}


        for market_type in MarketType:


            budget = self.db.query(
                func.sum(Market.budget)
            ).filter(
                Market.market_type == market_type
            ).scalar() or 0


            budget_by_type[
                market_type.value
            ] = budget





        # Budget par statut
        budget_by_status = {}


        for status in MarketStatus:


            budget = self.db.query(
                func.sum(Market.budget)
            ).filter(
                Market.status == status
            ).scalar() or 0


            budget_by_status[
                status.value
            ] = budget





        # Budget estimé
        estimated_total = self.db.query(
            func.sum(Market.estimated_amount)
        ).scalar() or 0



        # Budget final
        final_total = self.db.query(
            func.sum(Market.definitive_amount)
        ).filter(
            Market.definitive_amount.isnot(None)
        ).scalar() or 0




        return {

            "budget_by_type": budget_by_type,

            "budget_by_status": budget_by_status,

            "estimated_total": estimated_total,

            "final_total": final_total,


            "budget_variance":
                final_total - estimated_total,


            "budget_variance_percentage":

                round(

                    (
                        (
                            final_total -
                            estimated_total
                        )
                        /
                        estimated_total
                        *
                        100
                    )
                    if estimated_total > 0
                    else 0,

                    2
                )
        }





    def get_recent_activity(
        self,
        days: int = 7
    ) -> List[Dict]:
        """
        Récupère les activités récentes
        """

        from app.models.history import History



        cutoff_date = (
            datetime.now()
            -
            timedelta(days=days)
        )



        activities = self.db.query(
            History
        ).filter(
            History.created_at >= cutoff_date
        ).order_by(
            History.created_at.desc()
        ).limit(50).all()



        return [

            {

                "id": activity.id,

                "action": activity.action,

                "description": activity.description,

                "market_id": activity.market_id,

                "stage_id": activity.stage_id,

                "user_id": activity.user_id,

                "created_at":
                    activity.created_at.isoformat()
                    if activity.created_at
                    else None

            }

            for activity in activities

        ]


# -------------------------------------------------
# Factory du service statistiques
# -------------------------------------------------

def get_statistics_service(db: Session) -> StatisticsService:
    """
    Retourne une instance du service statistiques
    """
    return StatisticsService(db)