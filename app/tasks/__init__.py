"""
Module de tâches Celery
Tâches en arrière-plan pour les notifications et exports
"""

from app.tasks.celery_app import celery_app
from app.tasks.notification_tasks import check_delays, send_daily_report
from app.tasks.export_tasks import cleanup_old_files, backup_database

__all__ = [
    "celery_app",
    "check_delays",
    "send_daily_report",
    "cleanup_old_files",
    "backup_database",
]
