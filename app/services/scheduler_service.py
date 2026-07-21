"""
Service de planification des tâches
Gestion des tâches en arrière-plan pour les notifications et vérifications
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
import threading
import time

from app.database import SessionLocal
from app.services.notification_service import NotificationService
from app.services.export_service import ExportService
from app.config import settings
from app.utils.file_utils import cleanup_old_files
import os


class SchedulerService:
    """Service pour la planification des tâches en arrière-plan"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.db = None
    
    def start(self):
        """Démarre le planificateur de tâches"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.thread.start()
            print("Planificateur de tâches démarré")
    
    def stop(self):
        """Arrête le planificateur de tâches"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("Planificateur de tâches arrêté")
    
    def _run_scheduler(self):
        """Boucle principale du planificateur"""
        while self.running:
            try:
                # Créer une nouvelle session de base de données
                self.db = SessionLocal()
                
                # Exécuter les tâches planifiées
                self._check_delays()
                self._cleanup_old_files()
                self._backup_database()
                
                # Fermer la session
                self.db.close()
                
            except Exception as e:
                print(f"Erreur dans le planificateur: {e}")
                if self.db:
                    self.db.close()
            
            # Attendre avant la prochaine exécution (toutes les heures)
            time.sleep(3600)
    
    def _check_delays(self):
        """Vérifie les retards et met à jour les statuts"""
        try:
            notification_service = NotificationService(self.db)
            
            # Vérifier les retards des étapes
            stages_updated = notification_service.check_stage_delays()
            print(f"Vérification des retards: {stages_updated} étapes mises à jour")
            
            # Vérifier les retards des marchés
            markets_updated = notification_service.check_market_delays()
            print(f"Vérification des retards: {markets_updated} marchés mis à jour")
            
        except Exception as e:
            print(f"Erreur lors de la vérification des retards: {e}")
    
    def _cleanup_old_files(self):
        """Nettoie les anciens fichiers d'upload"""
        try:
            # Nettoyer les fichiers de plus de 30 jours
            deleted_count = cleanup_old_files(
                settings.UPLOAD_DIR, 
                days=settings.BACKUP_RETENTION_DAYS
            )
            print(f"Nettoyage des fichiers: {deleted_count} fichiers supprimés")
            
        except Exception as e:
            print(f"Erreur lors du nettoyage des fichiers: {e}")
    
    def _backup_database(self):
        """Crée une sauvegarde de la base de données"""
        try:
            # Créer une sauvegarde quotidienne
            backup_dir = settings.BACKUP_DIR
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Créer le répertoire de backup
            os.makedirs(backup_dir, exist_ok=True)
            
            # Copier le fichier de base de données SQLite
            db_path = settings.DATABASE_URL.replace("sqlite:///", "")
            if os.path.exists(db_path):
                import shutil
                backup_path = os.path.join(backup_dir, f"backup_{timestamp}.db")
                shutil.copy2(db_path, backup_path)
                print(f"Sauvegarde de la base de données: {backup_path}")
                
                # Nettoyer les anciennes sauvegardes
                self._cleanup_old_backups(backup_dir)
            
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la base de données: {e}")
    
    def _cleanup_old_backups(self, backup_dir: str):
        """Nettoie les anciennes sauvegardes"""
        try:
            cutoff_date = datetime.now() - timedelta(days=settings.BACKUP_RETENTION_DAYS)
            
            for filename in os.listdir(backup_dir):
                if filename.startswith("backup_") and filename.endswith(".db"):
                    filepath = os.path.join(backup_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    
                    if file_time < cutoff_date:
                        os.remove(filepath)
                        print(f"Ancienne sauvegarde supprimée: {filename}")
        
        except Exception as e:
            print(f"Erreur lors du nettoyage des sauvegardes: {e}")
    
    def run_once(self):
        """Exécute une fois toutes les tâches planifiées"""
        try:
            self.db = SessionLocal()
            
            self._check_delays()
            self._cleanup_old_files()
            self._backup_database()
            
            self.db.close()
            print("Tâches planifiées exécutées avec succès")
            
        except Exception as e:
            print(f"Erreur lors de l'exécution des tâches: {e}")
            if self.db:
                self.db.close()


# Instance globale du planificateur
scheduler_service = SchedulerService()


def get_scheduler_service() -> SchedulerService:
    """
    Retourne l'instance du service de planification
    
    Returns:
        Instance de SchedulerService
    """
    return scheduler_service


def start_scheduler():
    """Démarre le planificateur de tâches"""
    scheduler_service.start()


def stop_scheduler():
    """Arrête le planificateur de tâches"""
    scheduler_service.stop()
