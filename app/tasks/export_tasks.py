"""
Tâches Celery pour les exports et maintenance
Génération automatique de rapports et nettoyage
"""

from datetime import datetime, timedelta
from celery import current_task
from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.services.export_service import ExportService
from app.config import settings
import os
import shutil


@celery_app.task(bind=True)
def cleanup_old_files(self):
    """
    Nettoie les anciens fichiers d'upload
    Exécuté tous les jours
    """
    try:
        from app.utils.file_utils import cleanup_old_files
        
        deleted_count = cleanup_old_files(
            settings.UPLOAD_DIR,
            days=settings.BACKUP_RETENTION_DAYS
        )
        
        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


@celery_app.task(bind=True)
def backup_database(self):
    """
    Crée une sauvegarde de la base de données
    Exécuté tous les jours
    """
    try:
        backup_dir = settings.BACKUP_DIR
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Créer le répertoire de backup
        os.makedirs(backup_dir, exist_ok=True)
        
        # Copier le fichier de base de données SQLite
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        if os.path.exists(db_path):
            backup_path = os.path.join(backup_dir, f"backup_{timestamp}.db")
            shutil.copy2(db_path, backup_path)
            
            # Nettoyer les anciennes sauvegardes
            cutoff_date = datetime.now() - timedelta(days=settings.BACKUP_RETENTION_DAYS)
            
            for filename in os.listdir(backup_dir):
                if filename.startswith("backup_") and filename.endswith(".db"):
                    filepath = os.path.join(backup_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    
                    if file_time < cutoff_date:
                        os.remove(filepath)
            
            return {
                'status': 'success',
                'backup_path': backup_path,
                'timestamp': datetime.now().isoformat()
            }
        
        return {
            'status': 'error',
            'error': 'Database file not found',
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


@celery_app.task(bind=True)
def generate_monthly_report(self, month: int, year: int):
    """
    Génère un rapport mensuel automatiquement
    """
    try:
        db = SessionLocal()
        export_service = ExportService(db)
        
        # Générer le rapport Excel
        excel_file = export_service.export_dashboard_to_excel()
        
        # Sauvegarder le fichier
        reports_dir = os.path.join(settings.BACKUP_DIR, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        report_path = os.path.join(reports_dir, f"rapport_mensuel_{year}_{month}.xlsx")
        
        with open(report_path, 'wb') as f:
            f.write(excel_file.getvalue())
        
        db.close()
        
        return {
            'status': 'success',
            'report_path': report_path,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


@celery_app.task(bind=True)
def generate_market_report(self, market_id: int):
    """
    Génère un rapport détaillé pour un marché
    """
    try:
        db = SessionLocal()
        export_service = ExportService(db)
        
        # Générer le rapport Excel
        excel_file = export_service.export_market_to_excel(market_id)
        
        # Sauvegarder le fichier
        reports_dir = os.path.join(settings.BACKUP_DIR, 'markets')
        os.makedirs(reports_dir, exist_ok=True)
        
        report_path = os.path.join(reports_dir, f"marche_{market_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        
        with open(report_path, 'wb') as f:
            f.write(excel_file.getvalue())
        
        db.close()
        
        return {
            'status': 'success',
            'report_path': report_path,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
