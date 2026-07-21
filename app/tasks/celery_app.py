"""
Application Celery pour les tâches en arrière-plan
Configuration de Celery avec Redis
"""

from celery import Celery
from app.config import settings

# Création de l'application Celery
celery_app = Celery(
    'gestion_marches',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.tasks.notification_tasks', 'app.tasks.export_tasks']
)

# Configuration Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Africa/Casablanca',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Configuration des tâches planifiées
celery_app.conf.beat_schedule = {
    'check-delays-every-hour': {
        'task': 'app.tasks.notification_tasks.check_delays',
        'schedule': 3600.0,  # Toutes les heures
    },
    'cleanup-old-files-daily': {
        'task': 'app.tasks.export_tasks.cleanup_old_files',
        'schedule': 86400.0,  # Tous les jours
    },
    'backup-database-daily': {
        'task': 'app.tasks.export_tasks.backup_database',
        'schedule': 86400.0,  # Tous les jours
    },
    'send-daily-report': {
        'task': 'app.tasks.notification_tasks.send_daily_report',
        'schedule': 86400.0,  # Tous les jours
    },
}
