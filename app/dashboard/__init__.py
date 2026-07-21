"""
Dashboard module
Logique du tableau de bord, statistiques et KPIs
"""

from app.dashboard.statistics import StatisticsService
from app.dashboard.charts import ChartsService
from app.dashboard.kpis import KPIService

__all__ = [
    "StatisticsService",
    "ChartsService",
    "KPIService",
]
