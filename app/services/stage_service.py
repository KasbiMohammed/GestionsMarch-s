"""
Service de gestion des étapes
Logique métier pour la gestion des étapes des marchés
"""

from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.stage import Stage, StageStatus
from app.models.history import History


class StageService:
    """Service pour la gestion des étapes des marchés"""
    
    # Liste des étapes standard pour un marché public (40 étapes)
    STANDARD_STAGES = [
        "Identification du besoin",
        "Études techniques",
        "Estimation du coût",
        "Élaboration du CPS",
        "Élaboration du BPU",
        "Élaboration du DQE",
        "Validation technique",
        "Validation financière",
        "Validation juridique",
        "Programmation budgétaire",
        "Lancement de l'appel d'offres",
        "Publication sur le portail PMMP",
        "Réception des offres",
        "Ouverture des plis",
        "Vérification administrative",
        "Analyse technique",
        "Analyse financière",
        "Classement des entreprises",
        "Détection automatique des offres anormalement basses ou élevées",
        "Calcul automatique du prix de référence",
        "Génération automatique du rapport d'analyse",
        "Réunion de la commission",
        "Attribution provisoire",
        "Gestion des réclamations",
        "Attribution définitive",
        "Notification",
        "Approbation",
        "Visa",
        "Engagement",
        "Ordre de service",
        "Démarrage des travaux",
        "Suivi des travaux",
        "Réunions de chantier",
        "Décomptes",
        "Avenants",
        "Gestion des pénalités",
        "Réception provisoire",
        "Levée des réserves",
        "Réception définitive",
        "Clôture du marché"
    ]
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_stage(self, stage_data: dict, created_by: int) -> Stage:
        """
        Crée une nouvelle étape
        
        Args:
            stage_data: Données de l'étape
            created_by: ID de l'utilisateur créateur
            
        Returns:
            Étape créée
        """
        stage = Stage(**stage_data)
        stage.created_by = created_by
        stage.created_at = datetime.now()
        
        # Calculer le pourcentage initial
        stage.calculate_progress()
        
        self.db.add(stage)
        self.db.commit()
        self.db.refresh(stage)
        
        # Créer l'historique
        self._add_history(
            stage_id=stage.id,
            market_id=stage.market_id,
            action="Création",
            description=f"Création de l'étape '{stage.name}'",
            user_id=created_by
        )
        
        return stage
    
    def update_stage(self, stage_id: int, stage_data: dict, updated_by: int) -> Optional[Stage]:
        """
        Met à jour une étape
        
        Args:
            stage_id: ID de l'étape
            stage_data: Données à mettre à jour
            updated_by: ID de l'utilisateur modificateur
            
        Returns:
            Étape mise à jour ou None
        """
        stage = self.db.query(Stage).filter(Stage.id == stage_id).first()
        if not stage:
            return None
        
        # Sauvegarder les anciennes valeurs
        old_values = {key: getattr(stage, key) for key in stage_data.keys()}
        
        # Mettre à jour les champs
        for key, value in stage_data.items():
            if hasattr(stage, key) and key not in ['id', 'created_at', 'created_by']:
                setattr(stage, key, value)
        
        stage.updated_at = datetime.now()
        stage.updated_by = updated_by
        
        # Recalculer la progression et le retard
        stage.calculate_progress()
        stage.calculate_delay()
        
        self.db.commit()
        self.db.refresh(stage)
        
        # Créer l'historique
        self._add_history(
            stage_id=stage.id,
            market_id=stage.market_id,
            action="Modification",
            description=f"Mise à jour de l'étape '{stage.name}'",
            user_id=updated_by,
            old_values=old_values,
            new_values=stage_data
        )
        
        return stage
    
    def delete_stage(self, stage_id: int, deleted_by: int) -> bool:
        """
        Supprime une étape
        
        Args:
            stage_id: ID de l'étape
            deleted_by: ID de l'utilisateur supprimeur
            
        Returns:
            True si succès, False sinon
        """
        stage = self.db.query(Stage).filter(Stage.id == stage_id).first()
        if not stage:
            return False
        
        market_id = stage.market_id
        stage_name = stage.name
        
        self.db.delete(stage)
        self.db.commit()
        
        # Créer l'historique
        self._add_history(
            stage_id=stage_id,
            market_id=market_id,
            action="Suppression",
            description=f"Suppression de l'étape '{stage_name}'",
            user_id=deleted_by
        )
        
        return True
    
    def get_stage(self, stage_id: int) -> Optional[Stage]:
        """
        Récupère une étape par son ID
        
        Args:
            stage_id: ID de l'étape
            
        Returns:
            Étape ou None
        """
        return self.db.query(Stage).filter(Stage.id == stage_id).first()
    
    def get_stages_by_market(self, market_id: int) -> List[Stage]:
        """
        Récupère toutes les étapes d'un marché
        
        Args:
            market_id: ID du marché
            
        Returns:
            Liste des étapes
        """
        return self.db.query(Stage).filter(
            Stage.market_id == market_id
        ).order_by(Stage.order).all()
    
    def initialize_standard_stages(self, market_id: int, created_by: int) -> List[Stage]:
        """
        Initialise les étapes standard pour un marché
        
        Args:
            market_id: ID du marché
            created_by: ID de l'utilisateur créateur
            
        Returns:
            Liste des étapes créées
        """
        stages = []
        
        for index, stage_name in enumerate(self.STANDARD_STAGES, start=1):
            stage = Stage(
                market_id=market_id,
                name=stage_name,
                order=index,
                status=StageStatus.NOT_STARTED,
                progress_percentage=0,
                created_by=created_by,
                created_at=datetime.now()
            )
            
            self.db.add(stage)
            stages.append(stage)
        
        self.db.commit()
        
        # Rafraîchir les étapes
        for stage in stages:
            self.db.refresh(stage)
        
        return stages
    
    def update_stage_status(self, stage_id: int, status: StageStatus, 
                           updated_by: int, actual_date: datetime = None) -> Optional[Stage]:
        """
        Met à jour le statut d'une étape
        
        Args:
            stage_id: ID de l'étape
            status: Nouveau statut
            updated_by: ID de l'utilisateur
            actual_date: Date réelle de complétion
            
        Returns:
            Étape mise à jour ou None
        """
        stage = self.get_stage(stage_id)
        if not stage:
            return None
        
        old_status = stage.status
        stage.status = status
        
        if status == StageStatus.COMPLETED:
            stage.actual_date = actual_date or datetime.now()
            stage.progress_percentage = 100
        elif status == StageStatus.IN_PROGRESS:
            stage.progress_percentage = 50
        elif status == StageStatus.NOT_STARTED:
            stage.progress_percentage = 0
        
        stage.updated_at = datetime.now()
        stage.updated_by = updated_by
        
        stage.calculate_delay()
        
        self.db.commit()
        self.db.refresh(stage)
        
        # Créer l'historique
        self._add_history(
            stage_id=stage.id,
            market_id=stage.market_id,
            action="Changement de statut",
            description=f"Statut changé de {old_status.value} à {status.value}",
            user_id=updated_by
        )
        
        return stage
    
    def get_stages_by_status(self, market_id: int, status: StageStatus) -> List[Stage]:
        """
        Récupère les étapes d'un marché par statut
        
        Args:
            market_id: ID du marché
            status: Statut
            
        Returns:
            Liste des étapes
        """
        return self.db.query(Stage).filter(
            and_(
                Stage.market_id == market_id,
                Stage.status == status
            )
        ).all()
    
    def get_late_stages(self, market_id: int = None) -> List[Stage]:
        """
        Récupère les étapes en retard
        
        Args:
            market_id: ID du marché (optionnel)
            
        Returns:
            Liste des étapes en retard
        """
        query = self.db.query(Stage).filter(Stage.is_late == True)
        
        if market_id:
            query = query.filter(Stage.market_id == market_id)
        
        return query.all()
    
    def get_stage_statistics(self, market_id: int) -> Dict:
        """
        Récupère les statistiques d'étapes pour un marché
        
        Args:
            market_id: ID du marché
            
        Returns:
            Dictionnaire de statistiques
        """
        stages = self.get_stages_by_market(market_id)
        
        total = len(stages)
        by_status = {}
        
        for status in StageStatus:
            count = len([s for s in stages if s.status == status])
            by_status[status.value] = count
        
        avg_progress = sum(s.progress_percentage for s in stages) / total if total > 0 else 0
        late_count = len([s for s in stages if s.is_late])
        
        return {
            'total': total,
            'by_status': by_status,
            'average_progress': round(avg_progress, 2),
            'late_count': late_count,
            'completion_rate': round(by_status.get('completed', 0) / total * 100, 2) if total > 0 else 0
        }
    
    def reorder_stages(self, market_id: int, stage_orders: List[Dict], 
                      updated_by: int) -> bool:
        """
        Réordonne les étapes d'un marché
        
        Args:
            market_id: ID du marché
            stage_orders: Liste des {stage_id, order}
            updated_by: ID de l'utilisateur
            
        Returns:
            True si succès, False sinon
        """
        for item in stage_orders:
            stage = self.db.query(Stage).filter(
                and_(
                    Stage.id == item['stage_id'],
                    Stage.market_id == market_id
                )
            ).first()
            
            if stage:
                stage.order = item['order']
                stage.updated_at = datetime.now()
                stage.updated_by = updated_by
        
        self.db.commit()
        return True
    
    def _add_history(self, stage_id: int, market_id: int, action: str, 
                    description: str, user_id: int, old_values: dict = None, 
                    new_values: dict = None):
        """
        Ajoute une entrée d'historique
        
        Args:
            stage_id: ID de l'étape
            market_id: ID du marché
            action: Action effectuée
            description: Description
            user_id: ID de l'utilisateur
            old_values: Anciennes valeurs
            new_values: Nouvelles valeurs
        """
        history = History(
            market_id=market_id,
            stage_id=stage_id,
            action=action,
            description=description,
            user_id=user_id,
            old_values=old_values,
            new_values=new_values,
            created_at=datetime.now()
        )
        
        self.db.add(history)
        self.db.commit()


def get_stage_service(db: Session) -> StageService:
    """
    Factory pour créer une instance du service d'étapes
    
    Args:
        db: Session de base de données
        
    Returns:
        Instance de StageService
    """
    return StageService(db)
